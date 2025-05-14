import streamlit as st
import pandas as pd
from io import BytesIO
import io
import datetime
import random

st.set_page_config(page_title="Combined ITGC Application", layout="wide")
st.title("📊 Combined ITGC Application")

# User selection
module = st.radio("Select Module", ["Change Management", "Incident Management", "User Access Management"])

# -------------------------
# 🔁 CHANGE MANAGEMENT FLOW
# -------------------------
if module == "Change Management":
    uploaded_file = st.file_uploader("Upload Change Management File (CSV or Excel)", type=["csv", "xlsx"])

    if "df_checked" not in st.session_state:
        st.session_state.df_checked = None

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("Select Relevant Columns")
        columns = df.columns.tolist()
        col_request_id = st.selectbox("Request ID Column", columns)
        col_raised_date = st.selectbox("Raised Date Column", columns)
        col_resolved_date = st.selectbox("Resolved Date Column", columns)

        if st.button("Run Check"):
            df_checked = df.copy()
            df_checked = df_checked.rename(columns={
                col_request_id: "request_id",
                col_raised_date: "raised_date",
                col_resolved_date: "resolved_date"
            })

            df_checked["raised_date"] = pd.to_datetime(df_checked["raised_date"], errors='coerce')
            df_checked["resolved_date"] = pd.to_datetime(df_checked["resolved_date"], errors='coerce')

            df_checked["missing_raised"] = df_checked["raised_date"].isna()
            df_checked["missing_resolved"] = df_checked["resolved_date"].isna()
            df_checked["resolved_before_raised"] = df_checked["resolved_date"] < df_checked["raised_date"]
            df_checked["days_to_resolve"] = (df_checked["resolved_date"] - df_checked["raised_date"]).dt.days

            st.session_state.df_checked = df_checked

            st.subheader("📊 Summary of Findings")
            st.write(f"❌ Missing Raised Dates: {df_checked['missing_raised'].sum()}")
            st.write(f"❌ Missing Resolved Dates: {df_checked['missing_resolved'].sum()}")
            st.write(f"⚠️ Resolved Before Raised: {df_checked['resolved_before_raised'].sum()}")

            output = BytesIO()
            df_checked.to_excel(output, index=False)
            output.seek(0)
            st.download_button("📥 Download Full Data with Checks", data=output,
                               file_name="checked_change_management.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if st.session_state.df_checked is not None:
        st.subheader("📄 Full Data with Calculated Fields")
        st.dataframe(st.session_state.df_checked)

        st.subheader("🎯 Sampling Section")
        sampling_column = st.selectbox("Select Column for Sampling", st.session_state.df_checked.columns.tolist())
        sample_size = st.number_input("Number of Samples", min_value=1, max_value=len(st.session_state.df_checked), value=5, step=1)
        method = st.selectbox("Sampling Method", ["Top N (Longest)", "Bottom N (Quickest)", "Random"])

        if method == "Top N (Longest)":
            sample_df = st.session_state.df_checked.sort_values(by=sampling_column, ascending=False).head(sample_size)
        elif method == "Bottom N (Quickest)":
            sample_df = st.session_state.df_checked.sort_values(by=sampling_column, ascending=True).head(sample_size)
        else:
            sample_df = st.session_state.df_checked.sample(n=sample_size, random_state=1)

        st.write("📊 Sampled Records")
        st.dataframe(sample_df)

        sample_output = BytesIO()
        sample_df.to_excel(sample_output, index=False)
        sample_output.seek(0)
        st.download_button("📥 Download Sample Records", data=sample_output,
                           file_name="sampled_requests.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# -------------------------
# 🧯 INCIDENT MANAGEMENT FLOW
# -------------------------
elif module == "Incident Management":
    uploaded_file = st.file_uploader("Upload Incident Management File (Excel or CSV)", type=["csv", "xlsx"])

    def load_data(uploaded_file):
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.csv'):
                return pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                return pd.read_excel(uploaded_file)
        return None

    def calculate_date_differences(df, start_col, end_col, resolved_col):
        df[start_col] = pd.to_datetime(df[start_col], errors='coerce')
        df[resolved_col] = pd.to_datetime(df[resolved_col], errors='coerce')
        df[end_col] = pd.to_datetime(df[end_col], errors='coerce')
        df['Start-Resolved'] = (df[resolved_col] - df[start_col]).dt.days
        df['Resolved-Close'] = (df[end_col] - df[resolved_col]).dt.days
        return df

    if uploaded_file:
        df = load_data(uploaded_file)

        if df is not None:
            st.subheader("📋 Incident Management Columns")
            st.write("Data preview:", df.head())

            columns = df.columns
            start_col = st.selectbox("Select Start Date Column", columns)
            resolved_col = st.selectbox("Select Resolved Date Column", columns)
            end_col = st.selectbox("Select Close/End Date Column", columns)

            df = calculate_date_differences(df, start_col, end_col, resolved_col)

            st.write("✅ Updated Data with Date Differences:")
            st.dataframe(df)

            st.download_button("📥 Download Updated File", data=df.to_csv(index=False),
                               file_name="updated_incidents.csv", mime="text/csv")

# -------------------------
# 🔍 USER ACCESS FLOW
# -------------------------
elif module == "User Access Management":
    def read_file(uploaded_file, label):
        try:
            if uploaded_file.name.endswith(".csv"):
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
                    except Exception:
                        df = pd.read_csv(uploaded_file, encoding='windows-1252')
                if df.empty or df.columns.size == 0:
                    raise ValueError("No columns found in the CSV file.")
                st.write(f"### {label} (CSV Preview)")
                st.dataframe(df.head())
                return df
            else:
                sheets = pd.ExcelFile(uploaded_file).sheet_names
                selected_sheet = st.selectbox(f"Select sheet from {label}", sheets, key=label)
                df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                if df.empty or df.columns.size == 0:
                    raise ValueError("No columns found in the Excel sheet.")
                st.write(f"### {label} (Excel Preview - Sheet: {selected_sheet})")
                st.dataframe(df.head())
                return df
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return None

    # --- Mapping Step ---
    st.subheader("📂 Upload Files for Mapping")
    uploaded_hr_file = st.file_uploader("Upload HR Data File", type=["xlsx", "csv"], key="hr")
    uploaded_access_file = st.file_uploader("Upload User Access File", type=["xlsx", "csv"], key="access")
    uploaded_ad_file = st.file_uploader("Upload AD Data File (optional)", type=["xlsx", "csv"], key="ad")

    if uploaded_hr_file and uploaded_access_file:
        hr_df = read_file(uploaded_hr_file, "HR Data Preview")
        access_df = read_file(uploaded_access_file, "User Access Data Preview")

        if hr_df is not None and access_df is not None:
            # HR join selection
            hr_key = st.selectbox("Select Key Column in HR Data", hr_df.columns)
            access_hr_key = st.selectbox("Select Matching Column in User Access File (for HR)", access_df.columns)
            hr_columns = st.multiselect("Select HR Columns to Join", hr_df.columns.tolist(), default=[hr_key])
            if hr_key not in hr_columns:
                hr_columns.append(hr_key)
            hr_filtered = hr_df[hr_columns]
            access_df[access_hr_key] = access_df[access_hr_key].astype(str)
            hr_filtered[hr_key] = hr_filtered[hr_key].astype(str)
            matched_data = pd.merge(access_df, hr_filtered, left_on=access_hr_key, right_on=hr_key, how="left")
            if hr_key in matched_data.columns and hr_key != access_hr_key:
                matched_data.drop(columns=[hr_key], inplace=True)

            # Optional AD Join
            if uploaded_ad_file:
                ad_df = read_file(uploaded_ad_file, "AD Data Preview")
                if ad_df is not None:
                    ad_key = st.selectbox("Select Key Column in AD Data", ad_df.columns)
                    access_ad_key = st.selectbox("Select Matching Column in User Access File (for AD)", matched_data.columns)
                    ad_columns = st.multiselect("Select AD Columns to Join", ad_df.columns.tolist(), default=[ad_key])
                    if ad_key not in ad_columns:
                        ad_columns.append(ad_key)
                    ad_filtered = ad_df[ad_columns]
                    if ad_key in ad_filtered.columns and access_ad_key in matched_data.columns:
                        matched_data[access_ad_key] = matched_data[access_ad_key].astype(str)
                        ad_filtered[ad_key] = ad_filtered[ad_key].astype(str)
                        matched_data = pd.merge(matched_data, ad_filtered, left_on=access_ad_key, right_on=ad_key, how='left')
                        if ad_key in matched_data.columns and ad_key != access_ad_key:
                            matched_data.drop(columns=[ad_key], inplace=True)
                    else:
                        st.error("❌ Selected join keys not found in respective datasets.")

            st.markdown("---")
            st.subheader("✅ Final Merged Dataset")
            st.dataframe(matched_data.head())

            export_format = st.radio("Choose export format", ["Excel", "CSV"])
            if export_format == "Excel":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    matched_data.to_excel(writer, index=False, sheet_name="MappedData")
                st.download_button(
                    label="📥 Download Mapped File as Excel",
                    data=buffer.getvalue(),
                    file_name=f"Mapped_User_Access_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                csv_data = matched_data.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Mapped File as CSV",
                    data=csv_data,
                    file_name=f"Mapped_User_Access_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

            # --- Dormancy ---
            st.markdown("---")
            st.subheader("📅 Dormancy & GAP Analysis")

            date_col = st.selectbox("Select the Date Column for GAP Calculation", matched_data.columns)
            if date_col:
                try:
                    matched_data[date_col] = pd.to_datetime(matched_data[date_col], errors="coerce")
                    max_date = matched_data[date_col].max()
                    matched_data["GAP"] = (max_date - matched_data[date_col]).dt.days
                    st.success("✅ GAP column calculated and added.")
                except Exception as e:
                    st.error(f"Error processing GAP calculation: {e}")

            # --- AD-HR Join Date Difference ---
            st.markdown("---")
            st.subheader("📐 AD - HR Joining Date Difference")
            ad_join_col = st.selectbox("Select AD Joining Date Column", matched_data.columns, key="ad_date")
            hr_join_col = st.selectbox("Select HR Joining Date Column", matched_data.columns, key="hr_date")

            if ad_join_col and hr_join_col:
                try:
                    matched_data[ad_join_col] = pd.to_datetime(matched_data[ad_join_col], errors="coerce")
                    matched_data[hr_join_col] = pd.to_datetime(matched_data[hr_join_col], errors="coerce")
                    matched_data["AD-HR"] = (matched_data[ad_join_col] - matched_data[hr_join_col]).dt.days
                    st.success("✅ 'AD-HR' column calculated and added.")
                except Exception as e:
                    st.error(f"Error calculating AD-HR difference: {e}")

            st.subheader("📊 Final Data with GAP and AD-HR Columns")
            st.dataframe(matched_data.head())

            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine="xlsxwriter") as writer:
                matched_data.to_excel(writer, index=False, sheet_name="User Access Review")

            st.download_button(
                label="📥 Download Final File with GAP & AD-HR",
                data=output_buffer.getvalue(),
                file_name=f"User_Access_Reviewed_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- Random Sampling ---
            st.markdown("---")
            st.subheader("🎯 Random Sampling")
            sample_size = st.number_input("Enter number of random samples to extract", min_value=1, max_value=len(matched_data), value=5)

            if st.button("Generate Sample"):
                sample_df = matched_data.sample(n=sample_size, random_state=42)
                st.dataframe(sample_df)

                sample_buffer = io.BytesIO()
                with pd.ExcelWriter(sample_buffer, engine="xlsxwriter") as writer:
                    sample_df.to_excel(writer, index=False, sheet_name="RandomSample")

                st.download_button(
                    label="📥 Download Random Sample",
                    data=sample_buffer.getvalue(),
                    file_name=f"Random_Sample_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # --- Role Consistency Check for IT vs Non-IT ---
            st.markdown("---")
            st.subheader("🔐 IT vs Non-IT Access Validation")

            dept_col = st.selectbox("Select Department Column", matched_data.columns, key="dept_check")
            role_col = st.selectbox("Select Role/Access Column", matched_data.columns, key="role_check")

            if dept_col and role_col:
                try:
                    it_roles = set(matched_data[matched_data[dept_col].str.lower().str.contains("it|information technology|i\.t\.", case=False, na=False)][role_col].dropna().unique())
                    non_it_roles = set(matched_data[~matched_data[dept_col].str.lower().str.contains("it|information technology|i\.t\.", case=False, na=False)][role_col].dropna().unique())
                    common_roles = it_roles & non_it_roles

                    if common_roles:
                        flagged_df = matched_data[matched_data[role_col].isin(common_roles)]
                        st.warning("⚠️ Common roles found between IT and non-IT users:")
                        st.dataframe(flagged_df)

                        flagged_buffer = io.BytesIO()
                        with pd.ExcelWriter(flagged_buffer, engine="xlsxwriter") as writer:
                            flagged_df.to_excel(writer, index=False, sheet_name="IT_NonIT_Conflict")

                        st.download_button(
                            label="📥 Download Flagged Records",
                            data=flagged_buffer.getvalue(),
                            file_name=f"IT_NonIT_Conflicts_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.success("✅ No common roles between IT and non-IT users.")
                except Exception as e:
                    st.error(f"Error during IT vs Non-IT access comparison: {e}")