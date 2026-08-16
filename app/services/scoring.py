"""
===========================================================================
File: scoring.py

Project: ProcureMind AI
Author : Kavin Gupta

Purpose:
--------
This file contains the deterministic business logic used to compare
multiple vendor quotations.

The LLM will later extract data from RFQ and quotation PDFs, but all
financial calculations and ranking logic will be handled by Python.

This approach makes the procurement decision:

1. Accurate
2. Consistent
3. Explainable
4. Testable
5. Auditable

Main responsibilities:
----------------------
1. Calculate each vendor's total quotation price
2. Normalize vendor scores
3. Apply configurable scoring weights
4. Rank vendors using their final scores
5. Return the best vendor and complete ranking
===========================================================================
"""

# -------------------------------------------------------------------------
# Import schemas created in schemas.py
#
# VendorQuotation:
#   Represents the complete quotation submitted by one vendor.
#
# VendorScore:
#   Stores the calculated scores and rank of one vendor.
#
# ComparisonResult:
#   Stores the final best vendor and complete vendor ranking.
# -------------------------------------------------------------------------

from app.models.schemas import (
    ComparisonResult,
    VendorQuotation,
    VendorScore,
)


# -------------------------------------------------------------------------
# Scoring Weights
#
# These weights define the importance of each procurement factor.
#
# Price:
#   Given the highest importance because procurement teams generally
#   want to control purchasing cost.
#
# Delivery:
#   Measures how quickly the vendor can deliver the requested products.
#
# Compliance:
#   Measures how well the vendor satisfies the buyer's technical
#   requirements.
#
# Warranty:
#   Measures the warranty support offered by the vendor.
#
# Past Rating:
#   Measures the vendor's previous performance and reliability.
#
# Total:
#   Price        = 35%
#   Delivery     = 20%
#   Compliance   = 25%
#   Warranty     = 10%
#   Past Rating  = 10%
#
# Sum:
#   0.35 + 0.20 + 0.25 + 0.10 + 0.10 = 1.00
#
#   1.00 means 100%.
# -------------------------------------------------------------------------

WEIGHTS = {
    "price": 0.35,
    "delivery": 0.20,
    "compliance": 0.25,
    "warranty": 0.10,
    "past_rating": 0.10,
}


# -------------------------------------------------------------------------
# calculate_subtotal
#
# Purpose:
#   Calculates the total commercial value of one vendor quotation.
#
# Each vendor quotation may contain multiple products.
#
# Formula:
#   Item Total = Quoted Quantity × Unit Price
#
#   Quotation Subtotal = Sum of all item totals
#
# Example:
#   Laptop:
#       10 × 60000 = 600000
#
#   Monitor:
#       5 × 15000 = 75000
#
#   Subtotal:
#       600000 + 75000 = 675000
# -------------------------------------------------------------------------

def calculate_subtotal(
    quotation: VendorQuotation
) -> float:

    # Start the total quotation price from zero.
    subtotal = 0.0

    # Go through every product quoted by the vendor.
    for item in quotation.line_items:

        # Calculate the total price of the current product.
        #
        # Example:
        #   quoted_quantity = 10
        #   unit_price = 60000
        #
        #   item_total = 10 × 60000
        #              = 600000
        item_total = (
            item.quoted_quantity
            * item.unit_price
        )

        # Add the current product total to the quotation subtotal.
        subtotal = subtotal + item_total

    # Return the complete quotation price.
    return subtotal


# -------------------------------------------------------------------------
# calculate_lower_is_better_score
#
# Purpose:
#   Calculates a normalized score for factors where a lower value is better.
#
# Used for:
#   1. Price
#   2. Delivery days
#
# Why normalization is required:
#   Different factors use different units.
#
#   Price may be:
#       500000
#
#   Delivery may be:
#       10 days
#
#   We convert both into a common score between 0 and 100.
#
# Formula:
#   Score = Best Value / Current Value × 100
#
# Price example:
#   Lowest price = 500000
#   Current price = 600000
#
#   Score = 500000 / 600000 × 100
#         = 83.33
#
# Cheapest vendor:
#   Lowest price = 500000
#   Current price = 500000
#
#   Score = 500000 / 500000 × 100
#         = 100
#
# Therefore, the cheapest vendor receives a price score of 100.
# -------------------------------------------------------------------------

def calculate_lower_is_better_score(
    best_value: float,
    current_value: float
) -> float:

    # Safety check:
    # Division by zero is not allowed in Python.
    #
    # Pydantic already prevents zero prices and delivery days,
    # but this check makes the function independently safe.
    if current_value <= 0:
        return 0.0

    # Calculate the normalized score.
    score = (
        best_value
        / current_value
    ) * 100

    # Ensure that the score never becomes greater than 100.
    return min(
        score,
        100.0
    )


# -------------------------------------------------------------------------
# calculate_vendor_scores
#
# Purpose:
#   Compares all submitted vendor quotations.
#
# Main steps:
#   1. Ensure at least two quotations are available
#   2. Find the lowest quotation price
#   3. Find the fastest delivery
#   4. Find the highest warranty
#   5. Calculate individual vendor scores
#   6. Apply weights to every score
#   7. Calculate final weighted score
#   8. Sort vendors from highest to lowest score
#   9. Assign ranks
#   10. Return the best vendor and rankings
# -------------------------------------------------------------------------

def calculate_vendor_scores(
    quotations: list[VendorQuotation]
) -> ComparisonResult:

    # A comparison requires at least two vendors.
    #
    # One vendor cannot be meaningfully compared with itself.
    if len(quotations) < 2:
        raise ValueError(
            "At least two vendor quotations are required."
        )

    # ---------------------------------------------------------------------
    # Find the lowest total quotation price.
    #
    # calculate_subtotal() runs for every vendor quotation.
    #
    # Example:
    #   Vendor A = 600000
    #   Vendor B = 550000
    #   Vendor C = 650000
    #
    # Result:
    #   lowest_price = 550000
    # ---------------------------------------------------------------------

    lowest_price = min(
        calculate_subtotal(quotation)
        for quotation in quotations
    )

    # ---------------------------------------------------------------------
    # Find the fastest delivery time.
    #
    # Lower delivery days are better.
    #
    # Example:
    #   Vendor A = 12 days
    #   Vendor B = 9 days
    #   Vendor C = 18 days
    #
    # Result:
    #   fastest_delivery = 9
    # ---------------------------------------------------------------------

    fastest_delivery = min(
        quotation.delivery_days
        for quotation in quotations
    )

    # ---------------------------------------------------------------------
    # Find the highest warranty.
    #
    # Higher warranty is better.
    #
    # Example:
    #   Vendor A = 24 months
    #   Vendor B = 36 months
    #   Vendor C = 48 months
    #
    # Result:
    #   highest_warranty = 48
    # ---------------------------------------------------------------------

    highest_warranty = max(
        quotation.warranty_months
        for quotation in quotations
    )

    # This empty list will store the calculated score of every vendor.
    vendor_scores: list[VendorScore] = []

    # Process every quotation one by one.
    for quotation in quotations:

        # Calculate the current vendor's complete quotation value.
        subtotal = calculate_subtotal(
            quotation
        )

        # -----------------------------------------------------------------
        # Price Score
        #
        # Lower price is better.
        #
        # The cheapest vendor gets 100.
        #
        # Example:
        #   Lowest price = 500000
        #   Current price = 600000
        #
        #   Price score = 83.33
        # -----------------------------------------------------------------

        price_score = (
            calculate_lower_is_better_score(
                lowest_price,
                subtotal
            )
        )

        # -----------------------------------------------------------------
        # Delivery Score
        #
        # Lower delivery days are better.
        #
        # The fastest vendor receives 100.
        #
        # Example:
        #   Fastest delivery = 9 days
        #   Current delivery = 12 days
        #
        #   Delivery score = 9 / 12 × 100
        #                  = 75
        # -----------------------------------------------------------------

        delivery_score = (
            calculate_lower_is_better_score(
                fastest_delivery,
                quotation.delivery_days
            )
        )

        # -----------------------------------------------------------------
        # Compliance Score
        #
        # In Phase 1, this value comes directly from the quotation input.
        #
        # Example:
        #   technical_compliance_percent = 95
        #
        # Later, the Compliance Agent will automatically calculate it by
        # comparing RFQ requirements against the vendor quotation.
        # -----------------------------------------------------------------

        compliance_score = (
            quotation.technical_compliance_percent
        )

        # -----------------------------------------------------------------
        # Warranty Score
        #
        # Higher warranty is better.
        #
        # Formula:
        #   Current Warranty / Highest Warranty × 100
        #
        # Example:
        #   Current warranty = 36 months
        #   Highest warranty = 48 months
        #
        #   Warranty score = 36 / 48 × 100
        #                  = 75
        # -----------------------------------------------------------------

        if highest_warranty == 0:

            # If every vendor offers zero warranty, all vendors receive
            # the same warranty score.
            warranty_score = 100.0

        else:

            warranty_score = (
                quotation.warranty_months
                / highest_warranty
            ) * 100

        # -----------------------------------------------------------------
        # Past Rating Score
        #
        # Vendor rating is provided on a scale of 0 to 5.
        #
        # We convert it into a score out of 100.
        #
        # Formula:
        #   Vendor Rating / 5 × 100
        #
        # Example:
        #   Rating = 4.5
        #
        #   Score = 4.5 / 5 × 100
        #         = 90
        # -----------------------------------------------------------------

        past_rating_score = (
            quotation.past_rating
            / 5
        ) * 100

        # -----------------------------------------------------------------
        # Final Weighted Score
        #
        # Every individual score is multiplied by its configured weight.
        #
        # Formula:
        #
        #   Final Score =
        #       Price Score × 35%
        #       + Delivery Score × 20%
        #       + Compliance Score × 25%
        #       + Warranty Score × 10%
        #       + Past Rating Score × 10%
        #
        # Example:
        #   Price score      = 90
        #   Delivery score   = 80
        #   Compliance score = 95
        #   Warranty score   = 75
        #   Past rating      = 90
        #
        # Calculation:
        #   90 × 0.35 = 31.5
        #   80 × 0.20 = 16
        #   95 × 0.25 = 23.75
        #   75 × 0.10 = 7.5
        #   90 × 0.10 = 9
        #
        # Final score:
        #   31.5 + 16 + 23.75 + 7.5 + 9
        #   = 87.75
        # -----------------------------------------------------------------

        final_score = (
            price_score
            * WEIGHTS["price"]

            + delivery_score
            * WEIGHTS["delivery"]

            + compliance_score
            * WEIGHTS["compliance"]

            + warranty_score
            * WEIGHTS["warranty"]

            + past_rating_score
            * WEIGHTS["past_rating"]
        )

        # -----------------------------------------------------------------
        # Create a structured VendorScore object.
        #
        # round(value, 2):
        #   Stores every decimal value up to two decimal places.
        #
        # rank=0:
        #   The real rank is assigned after sorting all vendors.
        # -----------------------------------------------------------------

        vendor_score = VendorScore(
            vendor_name=quotation.vendor_name,

            subtotal=round(
                subtotal,
                2
            ),

            price_score=round(
                price_score,
                2
            ),

            delivery_score=round(
                delivery_score,
                2
            ),

            compliance_score=round(
                compliance_score,
                2
            ),

            warranty_score=round(
                warranty_score,
                2
            ),

            past_rating_score=round(
                past_rating_score,
                2
            ),

            final_score=round(
                final_score,
                2
            ),

            rank=0
        )

        # Add the current vendor's score to the score list.
        vendor_scores.append(
            vendor_score
        )

    # ---------------------------------------------------------------------
    # Sort Vendors
    #
    # key:
    #   Vendors are sorted using their final_score.
    #
    # reverse=True:
    #   Sorts scores in descending order.
    #
    # Result:
    #   Highest score first
    #   Lowest score last
    # ---------------------------------------------------------------------

    vendor_scores.sort(
        key=lambda vendor: vendor.final_score,
        reverse=True
    )

    # ---------------------------------------------------------------------
    # Assign Vendor Ranks
    #
    # Python indexes start from zero:
    #
    #   index 0 → rank 1
    #   index 1 → rank 2
    #   index 2 → rank 3
    #
    # Therefore:
    #   rank = index + 1
    # ---------------------------------------------------------------------

    for index in range(
        len(vendor_scores)
    ):

        vendor_scores[index].rank = (
            index + 1
        )

    # ---------------------------------------------------------------------
    # Return Final Comparison Result
    #
    # Because the score list has already been sorted:
    #
    #   vendor_scores[0]
    #
    # represents the highest-ranked vendor.
    # ---------------------------------------------------------------------

    return ComparisonResult(
        best_vendor=vendor_scores[0].vendor_name,
        rankings=vendor_scores
    )