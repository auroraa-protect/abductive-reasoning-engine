from app.model.enum_model import Severity


BANK_STATEMENT_FEATURE_REGISTRY = {

    # ============================================================
    # IMAGE FORENSICS
    # ============================================================

    # "image_forensics_available": {
    #     "title": "Image Forensics Availability",
    #     "category": "image",
    #     "severity": Severity.LOW,
    #     "action": "Review the available forensic analysis results where applicable.",
    #     "instruction": (
    #         "Indicate whether image forensic analysis was available. "
    #         "Do not treat unavailable image analysis as evidence of manipulation."
    #     )
    # },

    "ela": {
        "title": "Image Editing Traces",
        "category": "image",
        "severity": Severity.LOW,
        "action": "Review the original bank statement or source file.",
        "instruction": (
            "Discuss image-level editing traces without claiming that editing occurred."
        )
    },

    "exif_anomaly": {
        "title": "Document File Details",
        "category": "image",
        "severity": Severity.MEDIUM,
        "action": "Review the original file and its source.",
        "instruction": (
            "Discuss file details that warrant closer review without claiming "
            "a specific alteration."
        )
    },

    "fft": {
        "title": "Unusual Image Patterns",
        "category": "image",
        "severity": Severity.LOW,
        "action": "Review the original bank statement for visual consistency.",
        "instruction": (
            "Discuss unusual image patterns without identifying a specific manipulation."
        )
    },

    "noise": {
        "title": "Image Noise Patterns",
        "category": "image",
        "severity": Severity.LOW,
        "action": "Review the original document for visual consistency.",
        "instruction": (
            "Discuss image noise patterns without claiming a specific alteration."
        )
    },

    "cnn": {
        "title": "Overall Image Authenticity",
        "category": "image",
        "severity": Severity.HIGH,
        "action": "Review the original bank statement and confirm its source.",
        "instruction": (
            "Discuss overall image authenticity concerns without claiming "
            "the bank statement is forged."
        )
    },

    "resolution_dpi": {
        "title": "Image Quality",
        "category": "image",
        "severity": Severity.LOW,
        "action": "Review the original document or obtain a higher-quality copy.",
        "instruction": (
            "Discuss image quality only; do not treat low quality as proof "
            "of manipulation."
        )
    },


    # ============================================================
    # DOCUMENT / VISUAL MANIPULATION
    # ============================================================

    "logo_similarity": {
        "title": "Bank Logo",
        "category": "manipulation",
        "severity": Severity.HIGH,
        "action": "Verify the bank logo against an official bank-issued statement.",
        "instruction": (
            "State that the bank logo requires closer review without claiming "
            "that it is fake."
        )
    },

    "signature_similarity": {
        "title": "Signature",
        "category": "manipulation",
        "severity": Severity.HIGH,
        "action": "Verify the signature against a trusted original or bank record.",
        "instruction": (
            "State that the signature requires closer review without claiming "
            "that it is forged."
        )
    },

    "copy_move": {
        "title": "Signs of Copy-Paste Editing",
        "category": "manipulation",
        "severity": Severity.HIGH,
        "action": "Review the original bank statement for signs of editing.",
        "instruction": (
            "Discuss possible copy-paste editing indicators without claiming "
            "that editing definitely occurred."
        )
    },

    "font_inconsistency_score": {
        "title": "Font Consistency",
        "category": "manipulation",
        "severity": Severity.MEDIUM,
        "action": "Review the bank statement for consistent formatting.",
        "instruction": (
            "Discuss font consistency without identifying a specific edited field."
        )
    },

    "structural_anomaly": {
        "title": "Statement Structure",
        "category": "structure",
        "severity": Severity.HIGH,
        "action": "Compare the statement layout with a trusted bank-issued format.",
        "instruction": (
            "Discuss structural irregularities without claiming that the document "
            "is fraudulent."
        )
    },


    # ============================================================
    # IDENTITY / BANK DETAILS
    # ============================================================

    "pan_format": {
        "title": "PAN Details",
        "category": "identity",
        "severity": Severity.HIGH,
        "action": "Verify the PAN details against the submitted identity record.",
        "instruction": (
            "State that the PAN details require closer review without claiming "
            "that the PAN is invalid."
        )
    },

    "ifsc_validation": {
        "title": "Bank IFSC Code",
        "category": "banking",
        "severity": Severity.HIGH,
        "action": "Verify the IFSC and associated bank details against a trusted source.",
        "instruction": (
            "State that the Bank IFSC Code requires closer review without claiming "
            "that it is invalid."
        )
    },

    "bank_name_consistency": {
        "title": "Bank Name Consistency",
        "category": "banking",
        "severity": Severity.HIGH,
        "action": "Verify the bank name against a trusted bank record.",
        "instruction": (
            "State that the bank name requires closer review without claiming "
            "a specific mismatch."
        )
    },

    "bank_account_no_consistency": {
        "title": "Bank Account Number Consistency",
        "category": "banking",
        "severity": Severity.HIGH,
        "action": "Verify the account number against a trusted source.",
        "instruction": (
            "State that the bank account number requires closer review without "
            "claiming a specific mismatch."
        )
    },

    "employee_name_consistency": {
        "title": "Account Holder Name",
        "category": "identity",
        "severity": Severity.HIGH,
        "action": "Verify the account holder name against the submitted identity record.",
        "instruction": (
            "State that the account holder name requires closer review without "
            "claiming a specific mismatch."
        )
    },


    # ============================================================
    # DOCUMENT METADATA
    # ============================================================

    "metadata_modified": {
        "title": "Document File History",
        "category": "document",
        "severity": Severity.MEDIUM,
        "action": "Review the original file and its source.",
        "instruction": (
            "State that the document file history requires closer review without "
            "claiming that the file was deliberately altered."
        )
    },


    # ============================================================
    # BALANCE VALIDATION
    # ============================================================

    "opening_balance_validation": {
        "title": "Opening Balance",
        "category": "financial",
        "severity": Severity.HIGH,
        "action": "Verify the opening balance against the transaction history.",
        "instruction": (
            "State that the opening balance requires closer review without "
            "claiming a specific calculation error."
        )
    },

    "closing_balance_validation": {
        "title": "Closing Balance",
        "category": "financial",
        "severity": Severity.HIGH,
        "action": "Verify the closing balance against the transaction history.",
        "instruction": (
            "State that the closing balance requires closer review without "
            "claiming a specific calculation error."
        )
    },

    "running_balance_errors": {
        "title": "Running Balance Calculation",
        "category": "financial",
        "severity": Severity.HIGH,
        "action": "Review transaction entries and running balance calculations.",
        "instruction": (
            "State that the running balance calculations require closer review "
            "without claiming intentional manipulation."
        )
    },

    "balance_discontinuities": {
        "title": "Balance Continuity",
        "category": "financial",
        "severity": Severity.HIGH,
        "action": "Review the transaction sequence and balance progression.",
        "instruction": (
            "Discuss discontinuities in the balance progression without claiming "
            "that transactions were altered."
        )
    },

    "negative_balance_count": {
        "title": "Negative Balance Entries",
        "category": "financial",
        "severity": Severity.MEDIUM,
        "action": "Review negative balance entries against the bank transaction record.",
        "instruction": (
            "Discuss unusual negative balance occurrences without treating them "
            "as proof of document manipulation."
        )
    },


    # ============================================================
    # TRANSACTION TOTAL VALIDATION
    # ============================================================

    "debit_total_validation": {
        "title": "Total Debit Amount",
        "category": "transaction",
        "severity": Severity.HIGH,
        "action": "Verify total debit amounts against the listed transactions.",
        "instruction": (
            "State that the total debit calculation requires closer review without "
            "claiming a specific calculation error."
        )
    },

    "credit_total_validation": {
        "title": "Total Credit Amount",
        "category": "transaction",
        "severity": Severity.HIGH,
        "action": "Verify total credit amounts against the listed transactions.",
        "instruction": (
            "State that the total credit calculation requires closer review without "
            "claiming a specific calculation error."
        )
    },


    # ============================================================
    # TRANSACTION PATTERN ANALYSIS
    # ============================================================

    "duplicate_amount_count": {
        "title": "Repeated Transaction Amounts",
        "category": "transaction",
        "severity": Severity.MEDIUM,
        "action": "Review repeated transaction amounts in the transaction history.",
        "instruction": (
            "Discuss repeated transaction amounts as patterns requiring review "
            "without assuming that they are fraudulent."
        )
    },

    "missing_sequence_count": {
        "title": "Transaction Sequence",
        "category": "transaction",
        "severity": Severity.HIGH,
        "action": "Review the transaction sequence against the original bank statement.",
        "instruction": (
            "Discuss potential gaps in the transaction sequence without claiming "
            "that transactions were deliberately removed."
        )
    },


    # ============================================================
    # QR / BARCODE VALIDATION
    # ============================================================

    "qr_anomaly": {
        "title": "QR Code",
        "category": "verification",
        "severity": Severity.MEDIUM,
        "action": "Verify the QR code data against the issuing bank or trusted source.",
        "instruction": (
            "State that the QR code requires closer review without claiming "
            "that it is invalid or manipulated."
        )
    },

    "barcode_anamoly": {
        "title": "Barcode",
        "category": "verification",
        "severity": Severity.MEDIUM,
        "action": "Verify the barcode data against a trusted source where available.",
        "instruction": (
            "State that the barcode requires closer review without claiming "
            "that it is invalid or manipulated."
        )
    },
}