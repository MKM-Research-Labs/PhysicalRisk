# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Mortgage Common Data Model (CDM) implementation.
Based on exact specification from Mortgage_CDM v6.

This module provides a standardized data model for mortgage data,
enabling consistent processing across different data sources and applications.
"""

from typing import Dict, List

class MortgageCDM:
    """
    Mortgage Common Data Model (CDM) implementation.
    Provides a standardized schema and data transformation methods
    for mortgage data with comprehensive attributes.
    """
    def __init__(self):
        """Initialize the Mortgage CDM with complete schema definition."""
        self.schema = {
            "Mortgage": {
                "Header": {
                    "MortgageID": {
                        "type": "text",
                        "description": "Unique identifier for the mortgage loan"
                    },
                    "PropertyID": {
                        "type": "text",
                        "description": "Unique identifier for the contract"
                    },
                    "UPRN": {
                        "type": "text",
                        "description": "Unique Property Reference Number"
                    }
                },
                "Application": {
                    "MemberID": {
                        "type": "text",
                        "description": "Unique identifier for the borrower"
                    },
                    "MortgageProvider": {
                        "type": "text",
                        "description": "Financial institution providing the mortgage"
                    },
                    "ApplicationDate": {
                        "type": "date",
                        "description": "Date when the mortgage application was submitted"
                    },
                    "PreApprovalRequest": {
                        "type": "menu",
                        "options": ["Preapproval", "NotPreapproval"],
                        "description": "Indicates if application is for pre-approval"
                    },
                    "ApplicationChannel": {
                        "type": "menu",
                        "options": ["Retail", "Broker", "Correspondent"],
                        "description": "Channel through which the application was submitted"
                    },
                    "DenialReason": {
                        "type": "menu",
                        "options": ["Credit History", "DTI", "Collateral", "Other"],
                        "description": "Primary reason if application was denied"
                    },
                    "LoanPurpose": {
                        "type": "menu",
                        "options": ["Purchase", "Refinancing", "Home Improvement", "Other"],
                        "description": "Primary purpose of the mortgage loan"
                    },
                    "OccupancyType": {
                        "type": "menu",
                        "options": ["PrimaryResidence", "SecondResidence", "Investment"],
                        "description": "Intended occupancy status of the property"
                    },
                    "USRN": {
                        "type": "text",
                        "description": "Unique Street Reference Number"
                    },
                    "HMDALoanType": {
                        "type": "menu",
                        "options": ["Conventional", "FHA", "VA", "FSA"],
                        "description": "Type of loan as per HMDA classification"
                    },
                    "ApplicationPropertyValuation": {
                        "type": "decimal",
                        "description": "Estimated value of the property at application"
                    }
                },
                "FinancialTerms": {
                    "currency": {
                        "type": "text",
                        "description": "Currency code for the mortgage transaction"
                    },
                    "DisbursalDate": {
                        "type": "date",
                        "description": "Date when mortgage funds were released"
                    },
                    "PurchaseValue": {
                        "type": "decimal",
                        "description": "Agreed purchase price of the property"
                    },
                    "OriginalLoan": {
                        "type": "decimal",
                        "description": "Initial amount borrowed"
                    },
                    "OriginalTerm": {
                        "type": "integer",
                        "description": "Initial length of mortgage in months"
                    },
                    "TotalLoanCosts": {
                        "type": "decimal",
                        "description": "Total costs associated with the loan"
                    },
                    "OriginationCharges": {
                        "type": "decimal",
                        "description": "Fees charged for originating the loan"
                    },
                    "DiscountPoints": {
                        "type": "decimal",
                        "description": "Points paid to reduce interest rate"
                    },
                    "LenderCredits": {
                        "type": "decimal",
                        "description": "Credits provided by lender to offset costs"
                    },
                    "OriginalLendingRate": {
                        "type": "decimal",
                        "description": "Initial interest rate of the mortgage"
                    },
                    "OriginalSpread": {
                        "type": "decimal",
                        "description": "Difference between loan rate and reference rate"
                    },
                    "HMDARateSpread": {
                        "type": "decimal",
                        "description": "Rate spread as defined by HMDA"
                    },
                    "OriginalRateType": {
                        "type": "menu",
                        "options": ["Fixed", "Variable", "Tracker", "Discount", "Capped", "Standard Variable Rate"],
                        "description": "Type of interest rate structure"
                    },
                    "OriginalLTV": {
                        "type": "decimal",
                        "description": "Initial loan-to-value ratio"
                    },
                    "PrepaymentPenaltyTerm": {
                        "type": "integer",
                        "description": "Duration of prepayment penalty period"
                    },
                    "MaturityDate": {
                        "type": "date",
                        "description": "Scheduled date for final loan payment"
                    },
                    "OriginalBoEBase": {
                        "type": "decimal",
                        "description": "Bank of England base rate at origination"
                    },
                    "InitialFixedTerm": {
                        "type": "integer",
                        "description": "Duration in months of initial fixed rate period"
                    },
                    "EarlyRepaymentCharge": {
                        "type": "decimal",
                        "description": "Fee percentage for early repayment"
                    },
                    "ProductFee": {
                        "type": "decimal",
                        "description": "Fee charged for the mortgage product"
                    },
                    "DebtToIncomeRatio": {
                        "type": "decimal",
                        "description": "Ratio of total debt payments to income"
                    },
                    "LoanToValueRatio": {
                        "type": "decimal",
                        "description": "Ratio of loan amount to property value"
                    },
                    "IntroductoryRatePeriod": {
                        "type": "integer",
                        "description": "Duration in months of introductory rate period"
                    }
                },
                "Features": {
                    "MortgageType": {
                        "type": "menu",
                        "options": ["Residential", "Buy-to-Let", "Second Home", "Holiday Home", "Shared Ownership"],
                        "description": "Primary classification of mortgage type"
                    },
                    "PaymentFrequency": {
                        "type": "menu",
                        "options": ["Monthly", "Biweekly", "Weekly"],
                        "description": "How often payments are made"
                    },
                    "PortabilityFlag": {
                        "type": "boolean",
                        "description": "Indicates if mortgage can be transferred to new property"
                    },
                    "OverpaymentAllowance": {
                        "type": "decimal",
                        "description": "Maximum annual overpayment allowed without penalty"
                    },
                    "PaymentHolidayEligible": {
                        "type": "boolean",
                        "description": "Indicates if payment holidays are permitted"
                    },
                    "OffsetAccount": {
                        "type": "boolean",
                        "description": "Indicates if mortgage has linked offset account"
                    },
                    "SharedOwnershipShare": {
                        "type": "decimal",
                        "description": "Percentage owned in shared ownership scheme"
                    },
                    "HelpToBuyFlag": {
                        "type": "boolean",
                        "description": "Indicates if Help to Buy scheme is used"
                    },
                    "RightToBuyFlag": {
                        "type": "boolean",
                        "description": "Indicates if Right to Buy scheme is used"
                    },
                    "FirstTimeBuyerFlag": {
                        "type": "boolean",
                        "description": "Indicates if borrower is a first-time buyer"
                    },
                    "BalloonPayment": {
                        "type": "boolean",
                        "description": "Indicates if loan has final balloon payment"
                    },
                    "InterestOnlyPayment": {
                        "type": "boolean",
                        "description": "Indicates if payments are interest-only"
                    },
                    "NegativeAmortization": {
                        "type": "boolean",
                        "description": "Indicates if loan balance can increase"
                    },
                    "OtherNonAmortizingFeatures": {
                        "type": "boolean",
                        "description": "Indicates presence of other non-amortizing features"
                    }
                },
                "CurrentStatus": {
                    "LatestStatus": {
                        "type": "menu",
                        "options": ["Current", "Defaulted", "Completed", "Redeemed"],
                        "description": "Current status of the mortgage"
                    },
                    "PrincipalPayed": {
                        "type": "decimal",
                        "description": "Total principal amount repaid to date"
                    },
                    "InterestPayed": {
                        "type": "decimal",
                        "description": "Total interest amount paid to date"
                    },
                    "TotalPayments": {
                        "type": "integer",
                        "description": "Total number of payments made"
                    },
                    "OutstandingBalance": {
                        "type": "decimal",
                        "description": "Current loan balance"
                    },
                    "LastPaymentDate": {
                        "type": "date",
                        "description": "Date of most recent payment"
                    },
                    "InArrearsFlag": {
                        "type": "boolean",
                        "description": "Indicates if loan is currently in arrears"
                    },
                    "CurrentLTV": {
                        "type": "decimal",
                        "description": "Current loan-to-value ratio"
                    },
                    "CurrentBoEBase": {
                        "type": "decimal",
                        "description": "Current Bank of England base rate"
                    },
                    "CurrentLendingRate": {
                        "type": "decimal",
                        "description": "Current interest rate being charged"
                    },
                    "CurrentPayment": {
                        "type": "decimal",
                        "description": "Amount of current monthly payment"
                    },
                    "MissedPayments12M": {
                        "type": "integer",
                        "description": "Number of missed payments in last 12 months"
                    },
                    "HighestArrearsLast24M": {
                        "type": "decimal",
                        "description": "Highest arrears balance in last 24 months"
                    },
                    "PaymentHolidaysTaken": {
                        "type": "integer",
                        "description": "Number of payment holidays taken"
                    },
                    "LastPaymentHolidayDate": {
                        "type": "date",
                        "description": "Date of last payment holiday taken"
                    },
                    "TotalPaymentHolidays": {
                        "type": "integer",
                        "description": "Total number of payment holidays taken"
                    },
                    "ArrearsHighestBalance": {
                        "type": "decimal",
                        "description": "Highest historical arrears balance"
                    }
                },
                "Revaluation": {
                    "Revaluation1": {
                        "RevaluationTimestamp": {
                            "type": "timestamp",
                            "description": "Time revaluation was conducted"
                        },
                        "RevaluationSource": {
                            "type": "text",
                            "description": "System ID that is doing the calculation"
                        },
                        "RevaluationMortgage": {
                            "type": "decimal",
                            "description": "Model based value"
                        },
                        "RevaluationInterestRate": {
                            "type": "decimal",
                            "description": "Prevailing interest rate"
                        }
                    }
                },
                "Default": {
                    "DefaultFlag": {
                        "type": "boolean",
                        "description": "Indicates if loan has defaulted"
                    },
                    "DaysInArrears": {
                        "type": "integer",
                        "description": "Current number of days in arrears"
                    },
                    "DefaultDate": {
                        "type": "date",
                        "description": "Date when loan entered default"
                    },
                    "RestructureFlag": {
                        "type": "boolean",
                        "description": "Indicates if loan has been restructured"
                    },
                    "RestructureDate": {
                        "type": "date",
                        "description": "Date of loan restructuring"
                    },
                    "WriteOffAmount": {
                        "type": "decimal",
                        "description": "Amount written off due to default"
                    },
                    "RepossessionFlag": {
                        "type": "boolean",
                        "description": "Indicates if property has been repossessed"
                    },
                    "RepossessionDate": {
                        "type": "date",
                        "description": "Date of property repossession"
                    }
                },
                "BorrowerDetails": {
                    "MaritalStatus": {
                        "type": "menu",
                        "options": ["Single", "Married", "Divorced", "Widowed", "Civil Partnership", "Separated"],
                        "description": "Borrower's marital status"
                    },
                    "FamilyMembers": {
                        "type": "integer",
                        "description": "Number of family members in household"
                    },
                    "BorrowerIncome": {
                        "type": "decimal",
                        "description": "Borrower's annual income"
                    },
                    "BorrowerCreditScore": {
                        "type": "integer",
                        "description": "Borrower's credit score"
                    },
                    "BorrowerEmployment": {
                        "type": "menu",
                        "options": ["Employed", "Self-employed", "Retired", "Unemployed", "Student"],
                        "description": "Borrower's employment status"
                    },
                    "YearsInCurrentEmployment": {
                        "type": "integer",
                        "description": "Years at current employment"
                    },
                    "SecondaryIncome": {
                        "type": "decimal",
                        "description": "Additional annual income"
                    },
                    "IncomeVerificationType": {
                        "type": "menu",
                        "options": ["Payslips", "Bank Statements", "Tax Returns", "Self-Assessment", "Other"],
                        "description": "Method used to verify income"
                    },
                    "BorrowerAge": {
                        "type": "integer",
                        "description": "Age of primary borrower"
                    },
                    "BorrowerNationality": {
                        "type": "menu",
                        "options": ["UK", "EU", "Non-EU"],
                        "description": "Nationality of borrower"
                    },
                    "ResidencyStatus": {
                        "type": "menu",
                        "options": ["UK Citizen", "Permanent Resident", "Temporary Resident", "Other"],
                        "description": "Borrower's residency status"
                    }
                },
                "RiskMetrics": {
                    "AffordabilityRatio": {
                        "type": "decimal",
                        "description": "Ratio of income to mortgage payments"
                    },
                    "DebtServiceRatio": {
                        "type": "decimal",
                        "description": "Ratio of debt payments to income"
                    },
                    "StressTestRate": {
                        "type": "decimal",
                        "description": "Interest rate used for stress testing"
                    },
                    "RefinanceIncentive": {
                        "type": "integer",
                        "description": "Score indicating likelihood of refinancing (1-10)"
                    },
                    "PrepaymentRisk": {
                        "type": "integer",
                        "description": "Score indicating risk of early repayment (1-10)"
                    },
                    "BehavioralScore": {
                        "type": "integer",
                        "description": "Overall borrower behavior score (1-100)"
                    }
                },
                "HouseholdInsurance": {
                    "InsurerName": {
                        "type": "text",
                        "description": "Name of insurance company"
                    },
                    "InsurancePolicyID": {
                        "type": "text",
                        "description": "Insurance policy reference number"
                    }
                },
                "Regulatory": {
                    "Common": {
                        "BusinessOrCommercialPurpose": {
                            "type": "boolean",
                            "description": "Indicates if loan is for business purpose"
                        },
                        "FCAReferenceNumber": {
                            "type": "text",
                            "description": "Financial Conduct Authority reference number"
                        },
                        "AdvisedFlag": {
                            "type": "boolean",
                            "description": "Indicates if mortgage advice was provided"
                        },
                        "ExecutionOnlyFlag": {
                            "type": "boolean",
                            "description": "Indicates if mortgage was execution-only"
                        },
                        "ExecutionOnlyEligibilityFlag": {
                            "type": "boolean",
                            "description": "Indicates if customer eligible for execution-only"
                        },
                        "InteractiveSaleFlag": {
                            "type": "boolean",
                            "description": "Indicates if sale was interactive"
                        },
                        "DistanceMarketingFlag": {
                            "type": "boolean",
                            "description": "Indicates if distance marketing rules apply"
                        },
                        "RecordKeepingCompliantFlag": {
                            "type": "boolean",
                            "description": "Indicates compliance with record keeping rules"
                        },
                        "VulnerableCustomerFlag": {
                            "type": "boolean",
                            "description": "Indicates if customer is vulnerable"
                        }
                    },
                    "MCOB": {
                        "MMRCompliantFlag": {
                            "type": "boolean",
                            "description": "Compliant with Mortgage Market Review rules"
                        },
                        "CrossBorderPassportingFlag": {
                            "type": "boolean",
                            "description": "Indicates cross-border service provision"
                        },
                        "OriginatingMemberState": {
                            "type": "text",
                            "description": "Country where mortgage originated"
                        },
                        "ESISProvidedDate": {
                            "type": "date",
                            "description": "Date ESIS document provided"
                        },
                        "ESISVersion": {
                            "type": "text",
                            "description": "Version of ESIS document provided"
                        },
                        "CoolingOffPeriodDays": {
                            "type": "integer",
                            "description": "Length of cooling off period"
                        },
                        "ForeignCurrencyLoanFlag": {
                            "type": "boolean",
                            "description": "Indicates if loan is in foreign currency"
                        },
                        "ExchangeRateProtectionType": {
                            "type": "menu",
                            "options": ["None", "Cap", "Warning", "Right to Convert"],
                            "description": "Type of exchange rate protection"
                        },
                        "AdviceRejectionFlag": {
                            "type": "boolean",
                            "description": "Indicates if mortgage advice was rejected"
                        },
                        "AdviceRejectionReason": {
                            "type": "text",
                            "description": "Reason for rejecting mortgage advice"
                        },
                        "APRCInitialRate": {
                            "type": "decimal",
                            "description": "Initial Annual Percentage Rate of Charge"
                        },
                        "APRCSecondaryRate": {
                            "type": "decimal",
                            "description": "Secondary Annual Percentage Rate of Charge"
                        },
                        "StressTestCompliantFlag": {
                            "type": "boolean",
                            "description": "Indicates compliance with stress testing rules"
                        },
                        "AffordabilityAssessmentDate": {
                            "type": "date",
                            "description": "Date of affordability assessment"
                        },
                        "MortgageClubCode": {
                            "type": "text",
                            "description": "Code identifying mortgage club"
                        },
                        "IntermediaryCode": {
                            "type": "text",
                            "description": "Code identifying mortgage intermediary"
                        },
                        "InitialDisclosureProvidedDate": {
                            "type": "date",
                            "description": "Date initial disclosure provided"
                        },
                        "InitialDisclosureMethod": {
                            "type": "menu",
                            "options": ["Written", "Oral", "Both"],
                            "description": "Method of providing initial disclosure"
                        },
                        "CancellationRightsFlag": {
                            "type": "boolean",
                            "description": "Indicates if cancellation rights apply"
                        },
                        "SuitabilityAssessmentDate": {
                            "type": "date",
                            "description": "Date of suitability assessment"
                        },
                        "AdviceRetentionPeriod": {
                            "type": "integer",
                            "description": "Period for retaining advice records"
                        }
                    },
                    "HMDA": {
                        "HMDAReportableFlag": {
                            "type": "boolean",
                            "description": "Subject to HMDA reporting requirements"
                        },
                        "HMDAHOEPAStatus": {
                            "type": "boolean",
                            "description": "Subject to HOEPA requirements"
                        },
                        "HMDARateSpread": {
                            "type": "decimal",
                            "description": "HMDA rate spread calculation"
                        },
                        "ManufacturedHomeSecured": {
                            "type": "boolean",
                            "description": "Secured by manufactured/mobile home"
                        },
                        "ManufacturedHomeLandPropertyInterest": {
                            "type": "menu",
                            "options": ["DirectOwnership", "IndirectOwnership", "PaidLeasehold", "UnpaidLeasehold"],
                            "description": "Type of land interest for manufactured home"
                        }
                    }
                }
            }
        }

    def validate_mortgage(self, mortgage_data: dict) -> Dict[str, List[str]]:
        """
        Validates mortgage data against the CDM schema.
        Returns dictionary of validation errors by section.
        
        Args:
            mortgage_data: Mortgage data to validate
            
        Returns:
            Dictionary of validation errors by section
        """
        errors = {}
        
        try:
            # Validate Header section
            header_errors = []
            header = mortgage_data.get("Mortgage", {}).get("Header", {})
            for field in ["MortgageID", "PropertyID", "UPRN"]:
                if not header.get(field):
                    header_errors.append(f"Missing required field: {field}")
            if header_errors:
                errors["Header"] = header_errors
                
            # Validate Application section
            app_errors = []
            app = mortgage_data.get("Mortgage", {}).get("Application", {})
            
            # Validate menu fields
            menu_fields = {
                "PreApprovalRequest": ["Preapproval", "NotPreapproval"],
                "ApplicationChannel": ["Retail", "Broker", "Correspondent"],
                "DenialReason": ["Credit History", "DTI", "Collateral", "Other"],
                "LoanPurpose": ["Purchase", "Refinancing", "Home Improvement", "Other"],
                "OccupancyType": ["PrimaryResidence", "SecondResidence", "Investment"],
                "HMDALoanType": ["Conventional", "FHA", "VA", "FSA"]
            }
            
            for field, valid_options in menu_fields.items():
                if field in app and app[field] not in valid_options:
                    app_errors.append(f"Invalid value for {field}: {app[field]}")
                    
            # Validate Features section menu fields
            features = mortgage_data.get("Mortgage", {}).get("Features", {})
            features_menu_fields = {
                "MortgageType": ["Residential", "Buy-to-Let", "Second Home", "Holiday Home", "Shared Ownership"],
                "PaymentFrequency": ["Monthly", "Biweekly", "Weekly"]
            }
            
            for field, valid_options in features_menu_fields.items():
                if field in features and features[field] not in valid_options:
                    app_errors.append(f"Invalid value for Features.{field}: {features[field]}")
                    
            # Validate CurrentStatus section menu fields
            status = mortgage_data.get("Mortgage", {}).get("CurrentStatus", {})
            if "LatestStatus" in status:
                valid_statuses = ["Current", "Defaulted", "Completed", "Redeemed"]
                if status["LatestStatus"] not in valid_statuses:
                    app_errors.append(f"Invalid value for CurrentStatus.LatestStatus: {status['LatestStatus']}")
                    
            if app_errors:
                errors["Application"] = app_errors
                
            # Validate data relationships
            relationship_errors = self._validate_relationships(mortgage_data)
            if relationship_errors:
                errors.update(relationship_errors)
                
            return errors
            
        except Exception as e:
            return {"validation_error": [str(e)]}

    def _validate_relationships(self, mortgage_data: dict) -> Dict[str, List[str]]:
        """Validate relationships between mortgage fields."""
        errors = {}
        
        try:
            mortgage = mortgage_data.get("Mortgage", {})
            financial = mortgage.get("FinancialTerms", {})
            current = mortgage.get("CurrentStatus", {})
            features = mortgage.get("Features", {})
            borrower = mortgage.get("BorrowerDetails", {})
            
            # Validate LTV calculations
            purchase_value = financial.get("PurchaseValue")
            original_loan = financial.get("OriginalLoan")
            outstanding_balance = current.get("OutstandingBalance")
            
            if purchase_value and original_loan:
                calculated_original_ltv = original_loan / purchase_value
                reported_original_ltv = financial.get("OriginalLTV", 0)
                
                # Allow 1% tolerance for rounding
                if abs(calculated_original_ltv - reported_original_ltv) > 0.01:
                    errors.setdefault("LTV_Consistency", []).append(
                        f"Original LTV mismatch: calculated {calculated_original_ltv:.4f} vs reported {reported_original_ltv:.4f}"
                    )
            
            if purchase_value and outstanding_balance:
                calculated_current_ltv = outstanding_balance / purchase_value
                reported_current_ltv = current.get("CurrentLTV", 0)
                
                if abs(calculated_current_ltv - reported_current_ltv) > 0.01:
                    errors.setdefault("LTV_Consistency", []).append(
                        f"Current LTV mismatch: calculated {calculated_current_ltv:.4f} vs reported {reported_current_ltv:.4f}"
                    )
            
            # Validate mortgage type consistency
            mortgage_type = features.get("MortgageType")
            occupancy_type = mortgage.get("Application", {}).get("OccupancyType")
            
            if mortgage_type == "Buy-to-Let" and occupancy_type == "PrimaryResidence":
                errors.setdefault("Type_Consistency", []).append(
                    "Buy-to-Let mortgage should not have PrimaryResidence occupancy"
                )
            
            # Validate shared ownership consistency
            if mortgage_type == "Shared Ownership":
                shared_ownership_share = features.get("SharedOwnershipShare")
                if not shared_ownership_share or shared_ownership_share <= 0 or shared_ownership_share >= 1:
                    errors.setdefault("Shared_Ownership_Consistency", []).append(
                        "Shared Ownership mortgages must have valid ownership share (0 < share < 1)"
                    )
            
            # Validate age and employment consistency
            borrower_age = borrower.get("BorrowerAge")
            employment = borrower.get("BorrowerEmployment")
            years_employment = borrower.get("YearsInCurrentEmployment")
            
            if borrower_age and employment == "Retired" and borrower_age < 55:
                errors.setdefault("Employment_Consistency", []).append(
                    f"Borrower age {borrower_age} seems young for retirement"
                )
            
            if years_employment and borrower_age and years_employment > borrower_age - 16:
                errors.setdefault("Employment_Consistency", []).append(
                    f"Years in employment ({years_employment}) exceeds reasonable working years for age {borrower_age}"
                )
            
            # Validate default status consistency
            default_flag = mortgage.get("Default", {}).get("DefaultFlag")
            latest_status = current.get("LatestStatus")
            
            if default_flag and latest_status not in ["Defaulted"]:
                errors.setdefault("Default_Consistency", []).append(
                    "DefaultFlag is True but LatestStatus is not 'Defaulted'"
                )
            
            if latest_status == "Defaulted" and not default_flag:
                errors.setdefault("Default_Consistency", []).append(
                    "LatestStatus is 'Defaulted' but DefaultFlag is not True"
                )
                
        except Exception as e:
            errors["relationship_validation_error"] = [str(e)]
            
        return errors

    def create_mortgage_mapping(self, mort: dict) -> dict:
        """
        Creates a standardized mortgage data dictionary based on the CDM schema.
        
        Args:
            mort: Raw mortgage data dictionary
            
        Returns:
            Structured mortgage data according to CDM schema
        """
        try:
            mortgage_data = {
                # Header section
                'MortgageID': mort.get('Mortgage', {}).get('Header', {}).get('MortgageID'),
                'PropertyID': mort.get('Mortgage', {}).get('Header', {}).get('PropertyID'),
                'UPRN': mort.get('Mortgage', {}).get('Header', {}).get('UPRN'),
                
                # Application section
                'MemberID': mort.get('Mortgage', {}).get('Application', {}).get('MemberID'),
                'MortgageProvider': mort.get('Mortgage', {}).get('Application', {}).get('MortgageProvider'),
                'ApplicationDate': mort.get('Mortgage', {}).get('Application', {}).get('ApplicationDate'),
                'PreApprovalRequest': mort.get('Mortgage', {}).get('Application', {}).get('PreApprovalRequest'),
                'ApplicationChannel': mort.get('Mortgage', {}).get('Application', {}).get('ApplicationChannel'),
                'DenialReason': mort.get('Mortgage', {}).get('Application', {}).get('DenialReason'),
                'LoanPurpose': mort.get('Mortgage', {}).get('Application', {}).get('LoanPurpose'),
                'OccupancyType': mort.get('Mortgage', {}).get('Application', {}).get('OccupancyType'),
                'USRN': mort.get('Mortgage', {}).get('Application', {}).get('USRN'),
                'HMDALoanType': mort.get('Mortgage', {}).get('Application', {}).get('HMDALoanType'),
                'ApplicationPropertyValuation': mort.get('Mortgage', {}).get('Application', {}).get('ApplicationPropertyValuation'),
                
                # FinancialTerms section
                'currency': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('currency'),
                'DisbursalDate': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('DisbursalDate'),
                'PurchaseValue': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('PurchaseValue'),
                'OriginalLoan': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginalLoan'),
                'OriginalTerm': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginalTerm'),
                'TotalLoanCosts': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('TotalLoanCosts'),
                'OriginationCharges': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginationCharges'),
                'DiscountPoints': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('DiscountPoints'),
                'LenderCredits': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('LenderCredits'),
                'OriginalLendingRate': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginalLendingRate'),
                'OriginalSpread': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginalSpread'),
                'HMDARateSpread': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('HMDARateSpread'),
                'OriginalRateType': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginalRateType'),
                'OriginalLTV': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginalLTV'),
                'PrepaymentPenaltyTerm': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('PrepaymentPenaltyTerm'),
                'MaturityDate': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('MaturityDate'),
                'OriginalBoEBase': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('OriginalBoEBase'),
                'InitialFixedTerm': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('InitialFixedTerm'),
                'EarlyRepaymentCharge': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('EarlyRepaymentCharge'),
                'ProductFee': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('ProductFee'),
                'DebtToIncomeRatio': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('DebtToIncomeRatio'),
                'LoanToValueRatio': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('LoanToValueRatio'),
                'IntroductoryRatePeriod': mort.get('Mortgage', {}).get('FinancialTerms', {}).get('IntroductoryRatePeriod'),
                
                # Features section
                'MortgageType': mort.get('Mortgage', {}).get('Features', {}).get('MortgageType'),
                'PaymentFrequency': mort.get('Mortgage', {}).get('Features', {}).get('PaymentFrequency'),
                'PortabilityFlag': mort.get('Mortgage', {}).get('Features', {}).get('PortabilityFlag'),
                'OverpaymentAllowance': mort.get('Mortgage', {}).get('Features', {}).get('OverpaymentAllowance'),
                'PaymentHolidayEligible': mort.get('Mortgage', {}).get('Features', {}).get('PaymentHolidayEligible'),
                'OffsetAccount': mort.get('Mortgage', {}).get('Features', {}).get('OffsetAccount'),
                'SharedOwnershipShare': mort.get('Mortgage', {}).get('Features', {}).get('SharedOwnershipShare'),
                'HelpToBuyFlag': mort.get('Mortgage', {}).get('Features', {}).get('HelpToBuyFlag'),
                'RightToBuyFlag': mort.get('Mortgage', {}).get('Features', {}).get('RightToBuyFlag'),
                'FirstTimeBuyerFlag': mort.get('Mortgage', {}).get('Features', {}).get('FirstTimeBuyerFlag'),
                'BalloonPayment': mort.get('Mortgage', {}).get('Features', {}).get('BalloonPayment'),
                'InterestOnlyPayment': mort.get('Mortgage', {}).get('Features', {}).get('InterestOnlyPayment'),
                'NegativeAmortization': mort.get('Mortgage', {}).get('Features', {}).get('NegativeAmortization'),
                'OtherNonAmortizingFeatures': mort.get('Mortgage', {}).get('Features', {}).get('OtherNonAmortizingFeatures'),
                
                # CurrentStatus section
                'LatestStatus': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('LatestStatus'),
                'PrincipalPayed': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('PrincipalPayed'),
                'InterestPayed': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('InterestPayed'),
                'TotalPayments': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('TotalPayments'),
                'OutstandingBalance': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('OutstandingBalance'),
                'LastPaymentDate': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('LastPaymentDate'),
                'InArrearsFlag': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('InArrearsFlag'),
                'CurrentLTV': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('CurrentLTV'),
                'CurrentBoEBase': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('CurrentBoEBase'),
                'CurrentLendingRate': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('CurrentLendingRate'),
                'CurrentPayment': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('CurrentPayment'),
                'MissedPayments12M': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('MissedPayments12M'),
                'HighestArrearsLast24M': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('HighestArrearsLast24M'),
                'PaymentHolidaysTaken': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('PaymentHolidaysTaken'),
                'LastPaymentHolidayDate': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('LastPaymentHolidayDate'),
                'TotalPaymentHolidays': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('TotalPaymentHolidays'),
                'ArrearsHighestBalance': mort.get('Mortgage', {}).get('CurrentStatus', {}).get('ArrearsHighestBalance'),
                
                # Revaluation section
                'RevaluationTimestamp': mort.get('Mortgage', {}).get('Revaluation', {}).get('Revaluation1', {}).get('RevaluationTimestamp'),
                'RevaluationSource': mort.get('Mortgage', {}).get('Revaluation', {}).get('Revaluation1', {}).get('RevaluationSource'),
                'RevaluationMortgage': mort.get('Mortgage', {}).get('Revaluation', {}).get('Revaluation1', {}).get('RevaluationMortgage'),
                'RevaluationInterestRate': mort.get('Mortgage', {}).get('Revaluation', {}).get('Revaluation1', {}).get('RevaluationInterestRate'),
                
                # Default section
                'DefaultFlag': mort.get('Mortgage', {}).get('Default', {}).get('DefaultFlag'),
                'DaysInArrears': mort.get('Mortgage', {}).get('Default', {}).get('DaysInArrears'),
                'DefaultDate': mort.get('Mortgage', {}).get('Default', {}).get('DefaultDate'),
                'RestructureFlag': mort.get('Mortgage', {}).get('Default', {}).get('RestructureFlag'),
                'RestructureDate': mort.get('Mortgage', {}).get('Default', {}).get('RestructureDate'),
                'WriteOffAmount': mort.get('Mortgage', {}).get('Default', {}).get('WriteOffAmount'),
                'RepossessionFlag': mort.get('Mortgage', {}).get('Default', {}).get('RepossessionFlag'),
                'RepossessionDate': mort.get('Mortgage', {}).get('Default', {}).get('RepossessionDate'),
                
                # BorrowerDetails section
                'MaritalStatus': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('MaritalStatus'),
                'FamilyMembers': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('FamilyMembers'),
                'BorrowerIncome': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('BorrowerIncome'),
                'BorrowerCreditScore': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('BorrowerCreditScore'),
                'BorrowerEmployment': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('BorrowerEmployment'),
                'YearsInCurrentEmployment': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('YearsInCurrentEmployment'),
                'SecondaryIncome': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('SecondaryIncome'),
                'IncomeVerificationType': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('IncomeVerificationType'),
                'BorrowerAge': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('BorrowerAge'),
                'BorrowerNationality': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('BorrowerNationality'),
                'ResidencyStatus': mort.get('Mortgage', {}).get('BorrowerDetails', {}).get('ResidencyStatus'),
                
                # RiskMetrics section
                'AffordabilityRatio': mort.get('Mortgage', {}).get('RiskMetrics', {}).get('AffordabilityRatio'),
                'DebtServiceRatio': mort.get('Mortgage', {}).get('RiskMetrics', {}).get('DebtServiceRatio'),
                'StressTestRate': mort.get('Mortgage', {}).get('RiskMetrics', {}).get('StressTestRate'),
                'RefinanceIncentive': mort.get('Mortgage', {}).get('RiskMetrics', {}).get('RefinanceIncentive'),
                'PrepaymentRisk': mort.get('Mortgage', {}).get('RiskMetrics', {}).get('PrepaymentRisk'),
                'BehavioralScore': mort.get('Mortgage', {}).get('RiskMetrics', {}).get('BehavioralScore'),
                
                # HouseholdInsurance section
                'InsurerName': mort.get('Mortgage', {}).get('HouseholdInsurance', {}).get('InsurerName'),
                'InsurancePolicyID': mort.get('Mortgage', {}).get('HouseholdInsurance', {}).get('InsurancePolicyID'),
                
                # Regulatory.Common section
                'BusinessOrCommercialPurpose': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('BusinessOrCommercialPurpose'),
                'FCAReferenceNumber': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('FCAReferenceNumber'),
                'AdvisedFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('AdvisedFlag'),
                'ExecutionOnlyFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('ExecutionOnlyFlag'),
                'ExecutionOnlyEligibilityFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('ExecutionOnlyEligibilityFlag'),
                'InteractiveSaleFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('InteractiveSaleFlag'),
                'DistanceMarketingFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('DistanceMarketingFlag'),
                'RecordKeepingCompliantFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('RecordKeepingCompliantFlag'),
                'VulnerableCustomerFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('Common', {}).get('VulnerableCustomerFlag'),
                
                # Regulatory.MCOB section
                'MMRCompliantFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('MMRCompliantFlag'),
                'CrossBorderPassportingFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('CrossBorderPassportingFlag'),
                'OriginatingMemberState': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('OriginatingMemberState'),
                'ESISProvidedDate': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('ESISProvidedDate'),
                'ESISVersion': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('ESISVersion'),
                'CoolingOffPeriodDays': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('CoolingOffPeriodDays'),
                'ForeignCurrencyLoanFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('ForeignCurrencyLoanFlag'),
                'ExchangeRateProtectionType': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('ExchangeRateProtectionType'),
                'AdviceRejectionFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('AdviceRejectionFlag'),
                'AdviceRejectionReason': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('AdviceRejectionReason'),
                'APRCInitialRate': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('APRCInitialRate'),
                'APRCSecondaryRate': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('APRCSecondaryRate'),
                'StressTestCompliantFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('StressTestCompliantFlag'),
                'AffordabilityAssessmentDate': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('AffordabilityAssessmentDate'),
                'MortgageClubCode': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('MortgageClubCode'),
                'IntermediaryCode': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('IntermediaryCode'),
                'InitialDisclosureProvidedDate': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('InitialDisclosureProvidedDate'),
                'InitialDisclosureMethod': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('InitialDisclosureMethod'),
                'CancellationRightsFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('CancellationRightsFlag'),
                'SuitabilityAssessmentDate': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('SuitabilityAssessmentDate'),
                'AdviceRetentionPeriod': mort.get('Mortgage', {}).get('Regulatory', {}).get('MCOB', {}).get('AdviceRetentionPeriod'),
                
                # Regulatory.HMDA section
                'HMDAReportableFlag': mort.get('Mortgage', {}).get('Regulatory', {}).get('HMDA', {}).get('HMDAReportableFlag'),
                'HMDAHOEPAStatus': mort.get('Mortgage', {}).get('Regulatory', {}).get('HMDA', {}).get('HMDAHOEPAStatus'),
                'ManufacturedHomeSecured': mort.get('Mortgage', {}).get('Regulatory', {}).get('HMDA', {}).get('ManufacturedHomeSecured'),
                'ManufacturedHomeLandPropertyInterest': mort.get('Mortgage', {}).get('Regulatory', {}).get('HMDA', {}).get('ManufacturedHomeLandPropertyInterest'),
            }
            
            # Remove None values from the dictionary
            return {k: v for k, v in mortgage_data.items() if v is not None}
            
        except Exception as e:
            raise ValueError(f"Error creating mortgage mapping: {str(e)}")

    def get_schema_sections(self) -> List[str]:
        """Return list of all schema sections."""
        return list(self.schema["Mortgage"].keys())
    
    def get_section_fields(self, section: str) -> Dict[str, dict]:
        """Return all fields for a specific section."""
        return self.schema["Mortgage"].get(section, {})
    
    def get_menu_options(self, section: str, field: str) -> List[str]:
        """Return menu options for a specific field."""
        field_def = self.schema["Mortgage"].get(section, {}).get(field, {})
        return field_def.get("options", [])
    
    def validate_field_value(self, section: str, field: str, value) -> bool:
        """Validate a single field value against schema."""
        field_def = self.schema["Mortgage"].get(section, {}).get(field, {})
        
        if not field_def:
            return False
            
        field_type = field_def.get("type")
        
        if field_type == "menu":
            options = field_def.get("options", [])
            return value in options
        elif field_type == "boolean":
            return isinstance(value, bool)
        elif field_type == "integer":
            return isinstance(value, int)
        elif field_type == "decimal":
            return isinstance(value, (int, float))
        elif field_type in ["text", "date", "timestamp"]:
            return isinstance(value, str)
        
        return True