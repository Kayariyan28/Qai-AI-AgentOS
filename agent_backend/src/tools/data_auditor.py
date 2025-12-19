from langchain_core.tools import tool
import pandas as pd
import numpy as np
import os
import time
from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler
from collections import Counter

@tool("data_auditor")
def audit_and_save_data(instructions: str) -> str:
    """
    Generates synthetic data, audits quality, cleans/refines it, 
    saves to 'QData' folder, and produces an ETL diagram.
    """
    try:
        # 1. Generate Raw Data (Simulate "Raw" state with potential issues)
        # Intentionally create imbalanced data to demonstrate "Brushing up"
        X, y = make_classification(
            n_samples=500, 
            n_features=10, 
            n_informative=5, 
            n_redundant=2, 
            weights=[0.85, 0.15], # Imbalanced
            random_state=int(time.time())
        )
        
        df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(10)])
        df['target'] = y
        
        report = []
        report.append(">>> STEP 1: GENERATED RAW SYNTHETIC DATA")
        report.append(f"    Shape: {df.shape}")
        
        # 2. Audit Data
        report.append("\n>>> STEP 2: DATA AUDITOR CHECK")
        counts = Counter(y)
        minority_ratio = min(counts.values()) / sum(counts.values())
        
        audit_passed = True
        if minority_ratio < 0.3:
            report.append(f"    [!] AUDIT FAILED: Severe imbalance detected (Minority ratio: {minority_ratio:.2f})")
            audit_passed = False
        else:
            report.append("    [OK] Class balance acceptable.")
            
        std_devs = df.drop('target', axis=1).std()
        if std_devs.max() > 2.0 or std_devs.min() < 0.5:
             report.append("    [!] AUDIT WARNING: Feature scaling issues detected.")
             audit_passed = False # Strict audit
        else:
             report.append("    [OK] Feature scaling acceptable.")

        # 3. Brush Up / Refine
        if not audit_passed:
            report.append("\n>>> STEP 3: BRUSHING UP DATA (Refinement)")
            
            # Simple Oversampling for Balance
            max_size = max(counts.values())
            lst = [df]
            for class_index, group in df.groupby('target'):
                lst.append(group.sample(max_size-len(group), replace=True))
            df_balanced = pd.concat(lst)
            df = df_balanced
            report.append(f"    -> Applied Oversampling. New Shape: {df.shape}")
            
            # Scaling
            scaler = StandardScaler()
            features = [c for c in df.columns if c != 'target']
            df[features] = scaler.fit_transform(df[features])
            report.append("    -> Applied StandardScaler.")
            
            report.append("    [OK] DATA QUALIFIED AFTER BRUSH-UP.")
        else:
            report.append("\n>>> STEP 3: NO REFINEMENT NEEDED. DATA QUALIFIED.")

        # 4. Save to QData
        qdata_dir = os.path.join(os.getcwd(), "QData")
        os.makedirs(qdata_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"dataset_{timestamp}.csv"
        filepath = os.path.join(qdata_dir, filename)
        
        df.to_csv(filepath, index=False)
        report.append(f"\n>>> STEP 4: STORAGE")
        report.append(f"    Created 'QData' structured folder.")
        report.append(f"    [SYSTEM LOCATION] >>> {filepath}")

        # 5. ASCII ETL Diagram
        ascii_art = f"""
    +-----------------+       +------------------+       +------------------+
    |                 |       |                  |       |                  |
    |   RAW SOURCE    +------>+   DATA AUDITOR   +------>+   QData STORAGE  |
    | (Synthetic Gen) |       | (Audit & Clean)  |       |   (Qualified)    |
    |                 |       |                  |       |                  |
    +-----------------+       +---------+--------+       +------------------+
                                        |
                                        | status: {"QUALIFIED" if audit_passed else "REFINED -> QUALIFIED"}
                                        v
                                 +------+-------+
                                 |  ETL REPORT  |
                                 +--------------+
                                 | Samp: {len(df)}    |
                                 | Feat: 10     |
                                 | Bal:  Yes    |
                                 +--------------+
        """
        
        return "\n".join(report) + "\n\n" + ascii_art

    except Exception as e:
        import traceback
        return f"Error in Data Auditor: {str(e)}\n{traceback.format_exc()}"
