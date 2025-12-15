"""Processing page"""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import layout, info_box, metric_card
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from services.shared_utils import get_payroll_system
from services.data_mgt import DataManager
from services.edge_case_agent import EdgeCaseAgent


class ProcessingState(rx.State):
    """Processing page state"""
    
    enable_agent: bool = True
    processing_status: str = ""
    is_processing: bool = False
    agent_report: dict = {}
    
    async def process_payroll(self):
        """Process monthly payroll"""
        self.is_processing = True
        self.processing_status = "Processing..."
        
        company_state = await self.get_state(CompanyState)
        
        try:
            system = get_payroll_system()
            
            # Run main processing
            report = system.process_monthly_payroll(
                company_state.current_company,
                company_state.current_period
            )
            
            if report.get('success'):
                self.processing_status = "✅ Processing completed"
                
                # Run edge case agent if enabled
                if self.enable_agent:
                    data_state = await self.get_state(DataState)
                    data_state.load_period_data()
                    
                    import polars as pl
                    df = pl.DataFrame(data_state.processed_data)
                    
                    agent = EdgeCaseAgent(system.data_consolidator)
                    month, year = map(int, company_state.current_period.split('-'))
                    
                    modified_df, agent_report = agent.process_payroll(
                        df,
                        company_state.current_company,
                        month,
                        year
                    )
                    
                    # Save modified data
                    DataManager.save_period_data(
                        modified_df,
                        company_state.current_company,
                        month,
                        year
                    )
                    
                    self.agent_report = {
                        'automatic_count': agent_report.automatic_count,
                        'flagged_count': agent_report.flagged_count,
                        'anomalies': len(agent_report.anomalies),
                        'trends': len(agent_report.trends),
                    }
                    
                    # Reload data
                    data_state.load_period_data()
                    
                    self.processing_status = "✅ Processing and analysis completed"
            else:
                self.processing_status = f"❌ Error: {report.get('error', 'Unknown error')}"
                
        except Exception as e:
            self.processing_status = f"❌ Error: {str(e)}"
        finally:
            self.is_processing = False


def page() -> rx.Component:
    """Processing page layout"""
    return layout(
        rx.vstack(
            rx.heading("⚙️ Traitement des paies", size="7"),
            
            info_box(
                "Automatic Processing",
                "Calculate salaries according to Monaco legislation with intelligent case analysis",
                "settings",
            ),
            
            rx.divider(),
            
            rx.heading("Configuration", size="5"),
            
            rx.checkbox(
                "Enable intelligent agent",
                checked=ProcessingState.enable_agent,
                on_change=ProcessingState.set_enable_agent,
            ),
            
            rx.button(
                "Launch Processing",
                on_click=ProcessingState.process_payroll,
                size="3",
                color_scheme="blue",
                loading=ProcessingState.is_processing,
            ),
            
            rx.cond(
                ProcessingState.processing_status != "",
                rx.callout(
                    ProcessingState.processing_status,
                    icon="info",
                    size="2",
                ),
            ),
            
            rx.cond(
                ProcessingState.agent_report != {},
                rx.vstack(
                    rx.heading("🤖 Agent Report", size="4"),
                    rx.hstack(
                        metric_card(
                            "Automatic Modifications",
                            str(ProcessingState.agent_report.get('automatic_count', 0))
                        ),
                        metric_card(
                            "Flagged Cases",
                            str(ProcessingState.agent_report.get('flagged_count', 0))
                        ),
                        metric_card(
                            "Anomalies",
                            str(ProcessingState.agent_report.get('anomalies', 0))
                        ),
                        metric_card(
                            "Trends",
                            str(ProcessingState.agent_report.get('trends', 0))
                        ),
                        spacing="4",
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
            
            spacing="6",
            width="100%",
        ),
        AuthState,
    )
