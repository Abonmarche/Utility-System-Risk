import pandas as pd
import math
import plotly.express as px

def normalize_column(df, column_name):
    """
    Normalizes a column in the DataFrame to a scale from 1 to 10.
    Adds the normalized values in a new column with a suffix '_normalized'.
    
    :param df: DataFrame
    :param column_name: Name of the column to normalize (assumes it already exists in df)
    """
    min_value = df[column_name].min()
    max_value = df[column_name].max()
    normalized_col = column_name + '_normalized'

    if min_value == max_value:
        df[normalized_col] = df[column_name]
    else:
        df[normalized_col] = ((df[column_name] - min_value) * (9 / (max_value - min_value)) + 1).apply(math.ceil)
    return df

def create_heatmap(df, lof_col, cof_col, length_col):
    """
    Creates a plotly density heatmap of COF vs LOF, using length as the z-value.
    
    :param df: DataFrame containing the data
    :type df: pd.DataFrame
    :param lof_col: Name of the LOF column
    :type lof_col: str
    :param cof_col: Name of the COF column
    :type cof_col: str
    :param length_col: Name of the length column
    :type length_col: str
    """
    fig = px.density_heatmap(
        df,
        x=lof_col,
        y=cof_col,
        z=length_col,
        histfunc='sum',
        text_auto=True,
        nbinsx=11,
        nbinsy=11
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        width=900,
        height=750,
        margin=dict(t=50, l=50, r=50, b=50),
        coloraxis_colorbar=dict(title='sum of Length (Ft)')
    )
    fig.update_xaxes(range=[-0.5, 10.5])
    fig.update_yaxes(range=[-0.5, 10.5])
    return fig

#-------------------
# Decatur variables
# cof_file_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\DecaturResults\Final_COF.csv"
# lof_file_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\DecaturResults\Final_LOF.csv"
# risk_file_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\DecaturResults\Final_Risk.csv"

# unique_id = 'FACILITYID'
# length_column = 'LENGTH'
# image_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\DecaturResults\heatmap.html"
#-------------------

#-------------------
# Allegan variables
cof_file_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\AlleganThirdResults\Final_COF.csv"
lof_file_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\AlleganThirdResults\Final_LOF.csv"
risk_file_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\AlleganThirdResults\Final_Risk.csv"

unique_id = 'FACILITYID'
length_column = 'LENGTH'
image_path = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\AlleganThirdResults\heatmap.html"
#-------------------

cof_df = pd.read_csv(cof_file_path)
lof_df = pd.read_csv(lof_file_path)

# Convert all column names to uppercase
cof_df.columns = cof_df.columns.str.upper()
lof_df.columns = lof_df.columns.str.upper()

# Convert known column variables to uppercase
unique_id_upper = unique_id.upper()
length_column_upper = length_column.upper()

# Merge the dataframes on the uppercase unique ID
risk_df = pd.merge(cof_df, lof_df, on=unique_id_upper, suffixes=('_cof', '_lof'))

# Normalize COF and LOF columns
risk_df = normalize_column(risk_df, 'COF')
risk_df = normalize_column(risk_df, 'LOF')

# Create a risk score
risk_df['RISK_raw'] = risk_df['COF'] * risk_df['LOF']
risk_df['RISK_normalized'] = risk_df['COF_normalized'] * risk_df['LOF_normalized']

# Create and save the heatmap
plot = create_heatmap(risk_df, 'LOF_normalized', 'COF_normalized', length_column_upper)
plot.write_html(image_path)

risk_df.to_csv(risk_file_path, index=False)
