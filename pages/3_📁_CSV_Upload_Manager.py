import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="📁 CSV Upload Manager",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #ff6b6b 0%, #4ecdc4 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 2px dashed #dee2e6;
        margin: 1rem 0;
        text-align: center;
    }
    
    .data-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .info-card {
        background: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem;
    }
    
    .column-view {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        min-height: 500px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'data_history' not in st.session_state:
    st.session_state.data_history = []
if 'current_file_name' not in st.session_state:
    st.session_state.current_file_name = None
if 'data_analysis' not in st.session_state:
    st.session_state.data_analysis = None

# Main header
st.markdown("""
<div class="main-header">
    <h1>📁 CSV Upload & Data Manager</h1>
    <p>Upload, analyze, and manage your CSV data with advanced visualization</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for file management and settings
with st.sidebar:
    st.title("📂 File Management")
    
    # File upload section
    st.subheader("📤 Upload CSV File")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload your CSV file to analyze and manage data"
    )
    
    # File encoding options
    encoding = st.selectbox(
        "File Encoding",
        ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1'],
        help="Select the appropriate encoding for your CSV file"
    )
    
    # CSV parsing options
    st.subheader("⚙️ CSV Options")
    delimiter = st.selectbox("Delimiter", [',', ';', '\t', '|'], index=0)
    has_header = st.checkbox("Has header row", value=True)
    skip_rows = st.number_input("Skip rows", min_value=0, max_value=10, value=0)
    
    # Data processing options
    st.subheader("🔧 Data Processing")
    remove_empty_rows = st.checkbox("Remove empty rows", value=True)
    remove_empty_cols = st.checkbox("Remove empty columns", value=False)
    convert_types = st.checkbox("Auto-convert data types", value=True)
    
    # Display options
    st.subheader("📊 Display Options")
    max_display_rows = st.number_input("Max rows to display", min_value=10, max_value=10000, value=1000)
    show_data_types = st.checkbox("Show data types", value=True)
    show_statistics = st.checkbox("Show statistics", value=True)
    
    # File history
    st.subheader("📚 Upload History")
    if st.session_state.data_history:
        for i, item in enumerate(st.session_state.data_history[-5:]):  # Show last 5
            if st.button(f"📄 {item['name'][:20]}...", key=f"history_{i}"):
                st.session_state.uploaded_data = item['data']
                st.session_state.current_file_name = item['name']
                st.rerun()
    else:
        st.info("No upload history")

def analyze_data(df):
    """Perform comprehensive data analysis"""
    analysis = {
        'basic_info': {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'missing_values': df.isnull().sum().sum(),
            'duplicate_rows': df.duplicated().sum()
        },
        'column_info': {},
        'data_quality': {}
    }
    
    # Analyze each column
    for col in df.columns:
        col_data = df[col]
        analysis['column_info'][col] = {
            'dtype': str(col_data.dtype),
            'non_null_count': col_data.count(),
            'null_count': col_data.isnull().sum(),
            'unique_count': col_data.nunique(),
            'memory_usage': col_data.memory_usage(deep=True)
        }
        
        # Additional stats for numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            analysis['column_info'][col].update({
                'mean': col_data.mean(),
                'median': col_data.median(),
                'std': col_data.std(),
                'min': col_data.min(),
                'max': col_data.max(),
                'q25': col_data.quantile(0.25),
                'q75': col_data.quantile(0.75)
            })
        
        # Additional stats for text columns
        elif col_data.dtype == 'object':
            analysis['column_info'][col].update({
                'avg_length': col_data.astype(str).str.len().mean(),
                'max_length': col_data.astype(str).str.len().max(),
                'most_common': col_data.mode().iloc[0] if len(col_data.mode()) > 0 else None
            })
    
    return analysis

def process_uploaded_file(uploaded_file, encoding, delimiter, has_header, skip_rows, remove_empty_rows, remove_empty_cols, convert_types):
    """Process the uploaded CSV file"""
    try:
        # Read CSV with specified options
        df = pd.read_csv(
            uploaded_file,
            encoding=encoding,
            delimiter=delimiter,
            header=0 if has_header else None,
            skiprows=skip_rows
        )
        
        # Data cleaning
        if remove_empty_rows:
            df = df.dropna(how='all')
        
        if remove_empty_cols:
            df = df.dropna(axis=1, how='all')
        
        # Auto-convert data types
        if convert_types:
            for col in df.columns:
                # Try to convert to numeric
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass
                    
                    # Try to convert to datetime
                    try:
                        if df[col].dtype == 'object':
                            df[col] = pd.to_datetime(df[col], errors='ignore', infer_datetime_format=True)
                    except:
                        pass
        
        return df, None
        
    except Exception as e:
        return None, str(e)

# Main content area
if uploaded_file is not None:
    # Process the uploaded file
    with st.spinner("Processing uploaded file..."):
        df, error = process_uploaded_file(
            uploaded_file, encoding, delimiter, has_header, 
            skip_rows, remove_empty_rows, remove_empty_cols, convert_types
        )
    
    if error:
        st.markdown(f"""
        <div class="error-message">
            ❌ Error processing file: {error}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Store data in session state
        st.session_state.uploaded_data = df
        st.session_state.current_file_name = uploaded_file.name
        
        # Add to history
        history_item = {
            'name': uploaded_file.name,
            'data': df.copy(),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'size': len(df)
        }
        
        # Avoid duplicates in history
        if not any(item['name'] == uploaded_file.name for item in st.session_state.data_history):
            st.session_state.data_history.append(history_item)
        
        # Perform analysis
        st.session_state.data_analysis = analyze_data(df)
        
        st.markdown(f"""
        <div class="success-message">
            ✅ File "{uploaded_file.name}" uploaded successfully! 
            Loaded {len(df)} rows and {len(df.columns)} columns.
        </div>
        """, unsafe_allow_html=True)

# Display data if available
if st.session_state.uploaded_data is not None:
    df = st.session_state.uploaded_data
    analysis = st.session_state.data_analysis
    
    # Control buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📊 Refresh Analysis", use_container_width=True):
            st.session_state.data_analysis = analyze_data(df)
            st.rerun()
    
    with col2:
        if st.button("📈 Generate Charts", use_container_width=True):
            st.session_state.show_charts = True
    
    with col3:
        if st.button("🔍 Data Quality Report", use_container_width=True):
            st.session_state.show_quality = True
    
    with col4:
        # Export options
        export_format = st.selectbox("Export", ["CSV", "Excel", "JSON"], key="export_format")
        
    with col5:
        if st.button("💾 Download", use_container_width=True):
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"{st.session_state.current_file_name}_processed.csv",
                    "text/csv"
                )
            elif export_format == "Excel":
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                st.download_button(
                    "Download Excel",
                    buffer.getvalue(),
                    f"{st.session_state.current_file_name}_processed.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif export_format == "JSON":
                json_str = df.to_json(orient='records', indent=2)
                st.download_button(
                    "Download JSON",
                    json_str,
                    f"{st.session_state.current_file_name}_processed.json",
                    "application/json"
                )
    
    # Data overview metrics
    if analysis:
        st.markdown("### 📊 Data Overview")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Rows", f"{analysis['basic_info']['rows']:,}")
        with col2:
            st.metric("Total Columns", analysis['basic_info']['columns'])
        with col3:
            st.metric("Missing Values", f"{analysis['basic_info']['missing_values']:,}")
        with col4:
            st.metric("Duplicate Rows", f"{analysis['basic_info']['duplicate_rows']:,}")
        with col5:
            memory_mb = analysis['basic_info']['memory_usage'] / (1024 * 1024)
            st.metric("Memory Usage", f"{memory_mb:.2f} MB")
    
    # Create tabs for different views
    if len(df.columns) > 0:
        # Prepare tab names
        tab_names = ["📋 Full Dataset", "📊 Data Analysis"] + [f"📄 {col}" for col in df.columns[:12]]  # Limit to 12 columns + 2 main tabs
        tabs = st.tabs(tab_names)
        
        # Full dataset tab
        with tabs[0]:
            st.markdown("### 📊 Complete Dataset View")
            
            # Search and filter functionality
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Search across all columns:", placeholder="Enter search term...")
            with col2:
                search_columns = st.multiselect("Search in columns:", df.columns, default=list(df.columns))
            
            # Apply search filter
            display_data = df.copy()
            if search_term and search_columns:
                mask = pd.Series([False] * len(df))
                for col in search_columns:
                    if col in df.columns:
                        mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
                display_data = df[mask]
            
            # Limit rows for display
            if len(display_data) > max_display_rows:
                st.warning(f"Showing first {max_display_rows} rows of {len(display_data)} total rows")
                display_data = display_data.head(max_display_rows)
            
            # Display data with enhanced formatting
            st.dataframe(
                display_data,
                use_container_width=True,
                height=500
            )
            
            # Data types info
            if show_data_types:
                st.markdown("#### 📋 Column Information")
                col_info = pd.DataFrame({
                    'Column': df.columns,
                    'Data Type': [str(df[col].dtype) for col in df.columns],
                    'Non-Null Count': [df[col].count() for col in df.columns],
                    'Null Count': [df[col].isnull().sum() for col in df.columns],
                    'Unique Values': [df[col].nunique() for col in df.columns]
                })
                st.dataframe(col_info, use_container_width=True)
        
        # Data analysis tab
        with tabs[1]:
            st.markdown("### 📊 Data Analysis & Insights")
            
            if analysis:
                # Statistical summary for numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    st.markdown("#### 📈 Numeric Columns Summary")
                    st.dataframe(df[numeric_cols].describe(), use_container_width=True)
                
                # Missing values visualization
                if analysis['basic_info']['missing_values'] > 0:
                    st.markdown("#### 🔍 Missing Values Analysis")
                    missing_data = df.isnull().sum()
                    missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
                    
                    if len(missing_data) > 0:
                        fig = px.bar(
                            x=missing_data.index,
                            y=missing_data.values,
                            title="Missing Values by Column",
                            labels={'x': 'Columns', 'y': 'Missing Count'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Data distribution for numeric columns
                if len(numeric_cols) > 0:
                    st.markdown("#### 📊 Data Distribution")
                    selected_numeric_col = st.selectbox("Select column for distribution:", numeric_cols)
                    
                    if selected_numeric_col:
                        fig = px.histogram(
                            df,
                            x=selected_numeric_col,
                            title=f"Distribution of {selected_numeric_col}",
                            marginal="box"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Correlation matrix for numeric columns
                if len(numeric_cols) > 1:
                    st.markdown("#### 🔗 Correlation Matrix")
                    corr_matrix = df[numeric_cols].corr()
                    
                    fig = px.imshow(
                        corr_matrix,
                        title="Correlation Matrix",
                        color_continuous_scale="RdBu",
                        aspect="auto"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Individual column tabs (full-screen views)
        for i, col in enumerate(df.columns[:12], 2):  # Start from index 2 (after main tabs)
            if i < len(tabs):
                with tabs[i]:
                    st.markdown(f"""
                    <div class="column-view">
                        <h3>📄 {col} - Full Screen Analysis</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_data = df[col].dropna()
                    
                    # Column statistics
                    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                    
                    with col_stats1:
                        st.metric("Total Entries", len(df))
                    with col_stats2:
                        st.metric("Non-Null Entries", len(col_data))
                    with col_stats3:
                        st.metric("Unique Values", col_data.nunique() if len(col_data) > 0 else 0)
                    with col_stats4:
                        null_percentage = (len(df) - len(col_data)) / len(df) * 100 if len(df) > 0 else 0
                        st.metric("Null Percentage", f"{null_percentage:.1f}%")
                    
                    # Column-specific analysis
                    if pd.api.types.is_numeric_dtype(col_data):
                        # Numeric column analysis
                        st.markdown("#### 📊 Statistical Summary")
                        
                        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                        with stats_col1:
                            st.metric("Mean", f"{col_data.mean():.2f}" if len(col_data) > 0 else "N/A")
                        with stats_col2:
                            st.metric("Median", f"{col_data.median():.2f}" if len(col_data) > 0 else "N/A")
                        with stats_col3:
                            st.metric("Std Dev", f"{col_data.std():.2f}" if len(col_data) > 0 else "N/A")
                        with stats_col4:
                            st.metric("Range", f"{col_data.max() - col_data.min():.2f}" if len(col_data) > 0 else "N/A")
                        
                        # Distribution chart
                        st.markdown("#### 📈 Distribution")
                        fig = px.histogram(
                            col_data,
                            title=f"Distribution of {col}",
                            marginal="box",
                            nbins=50
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Box plot
                        fig_box = px.box(y=col_data, title=f"Box Plot of {col}")
                        st.plotly_chart(fig_box, use_container_width=True)
                    
                    else:
                        # Text/categorical column analysis
                        st.markdown("#### 📝 Text Analysis")
                        
                        if len(col_data) > 0:
                            text_stats1, text_stats2, text_stats3 = st.columns(3)
                            with text_stats1:
                                avg_length = col_data.astype(str).str.len().mean()
                                st.metric("Avg Length", f"{avg_length:.1f}")
                            with text_stats2:
                                max_length = col_data.astype(str).str.len().max()
                                st.metric("Max Length", max_length)
                            with text_stats3:
                                most_common = col_data.mode().iloc[0] if len(col_data.mode()) > 0 else "N/A"
                                st.metric("Most Common", str(most_common)[:20] + "..." if len(str(most_common)) > 20 else str(most_common))
                        
                        # Value frequency chart
                        st.markdown("#### 📊 Value Frequency")
                        value_counts = col_data.value_counts().head(20)
                        
                        if len(value_counts) > 0:
                            fig = px.bar(
                                x=value_counts.index.astype(str),
                                y=value_counts.values,
                                title=f"Top 20 Values in {col}",
                                labels={'x': 'Values', 'y': 'Frequency'}
                            )
                            fig.update_xaxes(tickangle=45)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Full column data display
                    st.markdown("#### 📋 Complete Data")
                    
                    # Search within column
                    col_search = st.text_input(f"🔍 Search in {col}:", key=f"search_{col}")
                    
                    # Create display DataFrame
                    col_display_df = pd.DataFrame({
                        'Row #': range(1, len(df) + 1),
                        col: df[col]
                    })
                    
                    # Apply search filter
                    if col_search:
                        mask = col_display_df[col].astype(str).str.contains(col_search, case=False, na=False)
                        col_display_df = col_display_df[mask]
                    
                    # Display with pagination
                    if len(col_display_df) > 1000:
                        st.warning(f"Showing first 1000 rows of {len(col_display_df)} matching rows")
                        col_display_df = col_display_df.head(1000)
                    
                    st.dataframe(
                        col_display_df,
                        use_container_width=True,
                        height=600,
                        column_config={
                            'Row #': st.column_config.NumberColumn("Row #", width="small"),
                            col: st.column_config.TextColumn(col, width="large")
                        }
                    )

else:
    # No data uploaded yet
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload Your CSV File</h3>
        <p>Drag and drop your CSV file in the sidebar or click to browse</p>
        <p>Supported formats: CSV files with various delimiters and encodings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sample data structure
    with st.expander("📋 Expected Data Structure Example"):
        sample_data = {
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'Email': ['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com'],
            'Book Description': ['Fantasy Novel', 'Romance Story', 'Sci-Fi Adventure', 'Mystery Thriller'],
            'Chapter 1': ['Complete', 'In Progress', 'Not Started', 'Complete'],
            'Chapter 2': ['Complete', 'Not Started', 'Not Started', 'In Progress'],
            'Chapter 3': ['In Progress', 'Not Started', 'Not Started', 'Not Started'],
            'Chapter 4': ['Not Started', 'Not Started', 'Not Started', 'Not Started'],
            'Chapter 5': ['Not Started', 'Not Started', 'Not Started', 'Not Started'],
            'Final PDF': ['Ready', 'Pending', 'Pending', 'Pending']
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)
        
        # Download sample
        csv_sample = sample_df.to_csv(index=False)
        st.download_button(
            "📥 Download Sample CSV",
            csv_sample,
            "sample_audiobook_data.csv",
            "text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    📁 CSV Upload & Data Manager | Advanced Data Analysis | 
    <a href="#" style="color: #ff6b6b;">Documentation</a> | 
    <a href="#" style="color: #4ecdc4;">Support</a>
</div>
""", unsafe_allow_html=True)

