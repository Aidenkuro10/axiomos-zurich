import time
from models.report import StrategicReport
from utils.logger import log

def generate_final_report(mission_id: str, deals: list, shared_storage=None):
    """
    Synthesizes findings into a strategic mission report for the LuxSoft UI.
    """
    # Telemetry notification for the final phase
    log(f"📋 Synthesizing strategic report for session {mission_id}...", "INFO", shared_storage, mission_id)
    
    # Count identified arbitrage opportunities
    total_deals = len([d for d in deals if d.high_value_signal])
    
    # Generate strategic summary
    if total_deals > 0:
        summary = f"Analysis complete. {total_deals} critical price anomalies identified. " \
                  f"The market exhibits unusual volatility for these specific models."
    else:
        summary = "Scan complete. No immediate arbitrage opportunities detected with current parameters. " \
                  "Continuous monitoring is recommended."

    # Calculate average market gap for the report
    prices = [d.listed_price for d in deals if d.listed_price > 0]
    avg_gap = 0.0
    if prices:
        # Calculate percentage spread as a market indicator
        avg_gap = (max(prices) - min(prices)) / max(prices) * 100

    # Build the final Pydantic model for the Frontend
    report = StrategicReport(
        mission_id=mission_id,
        opportunities_found=deals,
        summary=summary,
        average_market_gap=round(avg_gap, 2),
        status="completed"
    )

    log(f"✅ Report compiled successfully ({total_deals} opportunities).", "SUCCESS", shared_storage, mission_id)
    return report