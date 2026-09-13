from typing import Literal

from pydantic import BaseModel, Field


class CallAnalysisSchema(BaseModel):
    counterparty_name: str = Field(
        description="The company of the customer doing the dealing"
    )
    authorized_person: str = Field(description="Name of the customer in the dealing")
    amount: str = Field(
        description="The amount of currency in proper units to be part of the deal, for eg: if the customer wants to buy 1 million dollars, answer should be 1 million USD"
    )
    buy_or_sell: Literal["Buy", "Sell"] = Field(
        description="Whether the customer wants to buy or sell the mentioned currency."
    )
    deal_type: Literal["Cash", "Tom", "Spot", "Forward"] = Field(
        description="""The type of deal being made. The customer may say the deal outright or needs to be figured out from the maturity date.
        Rules:
        Today = Cash
        Today + 1 = Tom
        Today + 2 = Spot
        > Today + 2 = Forward
        """
    )
    customer_rate: str = Field(
        description="The rate at which the customer wants to buy/sell the currency. For eg: if someone wants to sell USD in INR it would be the rate of USR in INR. Will be said in the transcript"
    )
    spot_rate: str = Field(
        description="The current rate of the currency. For eg: if someone wants to sell USD in INR it would be the current rate of USR in INR. WIll be spoken in call"
    )
    currency_code: str = Field(
        description="The two currencies which the customer and agent are dealing with buying/selling. Assume the other currency in the deal to be INR unless otherwise specified for eg if the customer wants to sell 2 million USD the currency code would be USDINR."
    )

    maturity_date: str = Field(
        description="""
        The date on which the customer wants to buy/sell the mentioned currency, customer may say relative date like today, tomorrow or a week from now. If not mentioned then needs to be figured out by the deal type.
        Rules: 
        Cash = Today
        Tom = Tomorrow
        Spot = Day after Tomorrow
        """
    )

    exposure: Literal["Contractual Exposure", "Anticipated Exposure"] = Field(
        description="Whether the dealer has confirmed on the buy/sell of the currency or is still under anticipation. Will be spoken in the call."
    )

    mid_premia: str = Field(
        description="Will be spoken by the customer/dealer during the call. If not found leave empty"
    )
    confirmation_status: Literal["TRUE", "FALSE"] = Field(
        description="Whether the deal was confirmed or not at the end of the call."
    )
