SALARY_SLIP_FEATURE_REGISTRY = {

    # ============================================================
    # IMAGE FEATURES
    # ============================================================

    "ela": {
        "title": "Image Editing Traces",
        "category": "image",
        "priority": 3,
        "action": "Review the original document or source file.",
        "instruction": "Discuss image-level editing traces without claiming that editing occurred."
    },

    "exif_anomaly": {
        "title": "Document File Details",
        "category": "image",
        "priority": 2,
        "action": "Review the original file and its source.",
        "instruction": "Discuss file details that warrant closer review without claiming a specific alteration."
    },

    "fft": {
        "title": "Unusual Image Patterns",
        "category": "image",
        "priority": 3,
        "action": "Review the original document for visual consistency.",
        "instruction": "Discuss unusual image patterns without identifying a specific manipulation."
    },

    "noise": {
        "title": "Image Noise Patterns",
        "category": "image",
        "priority": 3,
        "action": "Review the original document for visual consistency.",
        "instruction": "Discuss image noise patterns without claiming a specific alteration."
    },

    "cnn": {
        "title": "Overall Image Authenticity",
        "category": "image",
        "priority": 1,
        "action": "Review the original document and confirm its source.",
        "instruction": "Discuss overall image authenticity concerns without claiming the document is forged."
    },

    "resolution_dpi": {
        "title": "Image Quality",
        "category": "image",
        "priority": 4,
        "action": "Review the original document or obtain a higher-quality copy.",
        "instruction": "Discuss image quality only; do not treat low quality as proof of manipulation."
    },


    # ============================================================
    # MANIPULATION DETECTION
    # ============================================================

    "logo_similarity": {
        "title": "Company Logo",
        "category": "manipulation",
        "priority": 2,
        "action": "Confirm the document source and company-issued copy.",
        "instruction": "State that the company logo requires closer review without claiming it is fake."
    },

    "signature_similarity": {
        "title": "Signature",
        "category": "manipulation",
        "priority": 1,
        "action": "Verify the signature against a trusted original or source.",
        "instruction": "State that the signature requires closer review without claiming it is forged."
    },

    "copy_move": {
        "title": "Signs of Copy-Paste Editing",
        "category": "manipulation",
        "priority": 1,
        "action": "Review the original document for signs of editing.",
        "instruction": "Discuss possible copy-paste editing indicators without claiming that editing definitely occurred."
    },

    "font_inconsistency_score": {
        "title": "Font Consistency",
        "category": "manipulation",
        "priority": 2,
        "action": "Review the original document for consistent formatting.",
        "instruction": "Discuss font consistency without identifying a specific edited field."
    },


    # ============================================================
    # ARITHMETIC / PAYROLL CHECKS
    # ============================================================

    "gross_earnings_validation": {
        "title": "Gross Earnings",
        "category": "payroll",
        "priority": 1,
        "action": "Verify the gross earnings against the original payroll record.",
        "instruction": "State that the gross earnings require closer review without claiming a specific calculation error."
    },

    "net_pay_validation": {
        "title": "Net Pay",
        "category": "payroll",
        "priority": 1,
        "action": "Verify the net pay against the original payroll calculation.",
        "instruction": "State that the net pay requires closer review without claiming a specific calculation error."
    },

    "total_deductions_validation": {
        "title": "Total Deductions",
        "category": "payroll",
        "priority": 1,
        "action": "Verify the deductions against the original payroll calculation.",
        "instruction": "State that the total deductions require closer review without claiming a specific calculation error."
    },


    # ============================================================
    # IDENTITY / BANK DETAILS
    # ============================================================

    "pan_format": {
        "title": "PAN Details",
        "category": "identity",
        "priority": 1,
        "action": "Verify the PAN details against the submitted identity record.",
        "instruction": "State that the PAN details require closer review without claiming the PAN is invalid."
    },

    "uan_format": {
        "title": "UAN Number",
        "category": "identity",
        "priority": 2,
        "action": "Verify the UAN against the employee's employment record.",
        "instruction": "State that the UAN requires closer review without claiming that the number is invalid."
    },

    "ifsc_validation": {
        "title": "Bank IFSC Code",
        "category": "banking",
        "priority": 1,
        "action": "Verify the IFSC and associated bank details against a trusted source.",
        "instruction": "State that the Bank IFSC Code requires closer review without claiming that it is invalid."
    },

    "bank_name_consistency": {
        "title": "Bank Name",
        "category": "banking",
        "priority": 1,
        "action": "Verify the bank name against the original document or trusted bank record.",
        "instruction": "State that the bank name requires closer review without claiming a specific mismatch."
    },

    "bank_account_no_consistency": {
        "title": "Bank Account Number",
        "category": "banking",
        "priority": 1,
        "action": "Verify the account number against a trusted source.",
        "instruction": "State that the bank account number requires closer review without claiming a specific mismatch."
    },

    "employee_name_consistency": {
        "title": "Employee Name",
        "category": "identity",
        "priority": 1,
        "action": "Verify the employee name against the submitted identity or employment record.",
        "instruction": "State that the employee name requires closer review without claiming a specific mismatch."
    },


    # ============================================================
    # DATE / EMPLOYMENT DETAILS
    # ============================================================

    "metadata_modified": {
        "title": "Document File History",
        "category": "document",
        "priority": 2,
        "action": "Review the original file and its source.",
        "instruction": "State that the document file history requires closer review without claiming that the file was deliberately altered."
    },

    "joining_date_validation": {
        "title": "Joining Date",
        "category": "employment",
        "priority": 2,
        "action": "Verify the joining date against the employee's employment record.",
        "instruction": "State that the joining date requires closer review without claiming a specific date discrepancy."
    },

    "days_worked_validation": {
        "title": "Days Worked",
        "category": "payroll",
        "priority": 2,
        "action": "Verify the reported days worked against the payroll record.",
        "instruction": "State that the days worked requires closer review without claiming a specific discrepancy."
    },

    "hra_ratio_check": {
        "title": "HRA Amount",
        "category": "payroll",
        "priority": 2,
        "action": "Verify the HRA amount against the original payroll calculation.",
        "instruction": "State that the HRA amount requires closer review without claiming a specific calculation error."
    }
}