from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class PaymentInstallment(BaseModel):
    name: str = Field(..., description="E.g., 'On Application', 'First Call'")
    percentage: float = Field(..., description="Percentage of the total rights price")
    amount: float = Field(..., description="Exact monetary amount per share")
    due_date: Optional[date] = Field(None, description="Due date for this installment")

class PaymentSchedule(BaseModel):
    is_partly_paid: bool = Field(default=False)
    ticker_symbol: Optional[str] = Field(None, description="Ticker for partly paid shares, e.g., RELIANCE-PP")
    installments: List[PaymentInstallment] = []

class RetailAllocationRules(BaseModel):
    green_shoe_option_retained: bool = Field(default=False, description="Did the board retain oversubscription?")
    promoter_renunciation_percentage: float = Field(default=0.0, description="Percentage of rights promoters renounced")
    retail_carve_out_percentage: Optional[float] = Field(None, description="Specific retail carve-out if any")

class RightsIssueDetails(BaseModel):
    symbol: str
    company_name: str
    base_issue_size_crores: float
    old_shares_ratio: int = Field(..., description="The 'for every X shares held' part of the ratio")
    new_shares_ratio: int = Field(..., description="The 'you get Y shares' part of the ratio")
    issue_price: float
    current_market_price: float

class RightsIssueTimeline(BaseModel):
    announcement_date: Optional[date] = None
    board_meeting_date: Optional[date] = None
    board_approval_date: Optional[date] = None
    dlof_filing_date: Optional[date] = None
    record_date: Optional[date] = None
    lof_dispatch_date: Optional[date] = None
    open_date: Optional[date] = None
    renunciation_date: Optional[date] = None
    close_date: Optional[date] = None
    allotment_date: Optional[date] = None
    refund_unblock_date: Optional[date] = None
    trading_approval_date: Optional[date] = None
    listing_date: Optional[date] = None

class RightsIssue(BaseModel):
    details: RightsIssueDetails
    timeline: RightsIssueTimeline
    payment_schedule: PaymentSchedule
    retail_rules: RetailAllocationRules
