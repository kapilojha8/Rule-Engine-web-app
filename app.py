# using flask_restful
from flask import Flask, jsonify, request

import mysql.connector
import pandas as pd

from flask import  render_template

# creating the flask app
app = Flask(__name__)
app.static_folder = 'static'

def Connect_with_db_get_df():
    connection = mysql.connector.connect(
        host='localhost',
        user='ritik',
        password='MRpark@1234',
        database='MR_MT_DB'
    )

    # Create a cursor
    cursor = connection.cursor()

    # Execute a query
    query = "SELECT * FROM TireData"
    cursor.execute(query)

    # Fetch all rows
    rows = cursor.fetchall()

    # Get column names
    column_names = [i[0] for i in cursor.description]

    # Create a DataFrame
    df_raw = pd.DataFrame(rows, columns=column_names)

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Display the DataFrame
    return df_raw


@app.route('/n_months_predictions/', methods=['GET'])
def get_n_months_predictions():
    n_months_param = request.args.get('months')
    df_raw = Connect_with_db_get_df()
    raw_unique_all_Tire_ids = df_raw['Vehicle_Asset_Number'].unique()
    ThresholdTread = 1.6
    result_prediction = []
    for val in raw_unique_all_Tire_ids:
        # Extract the number of months from the payload 
        # Filter the 'df_raw' DataFrame for the current Tire ID
        # Calculate the average kilometers driven per month for the current Tire ID
        # Estimate the kilometers to be driven in the next 'N_months' based on the average
        # Predict the total kilometers driven after 'N_months'
        
        N_months = int(n_months_param)
        df = df_raw.loc[df_raw['Vehicle_Asset_Number'] == val].copy()
        avg_km_driven_p_month = (max(df['Km_driven'])+min(df['Km_driven']))/df.shape[0]
        km_for_next_n_month = N_months*avg_km_driven_p_month
        Predict_kms = max(df['Km_driven'])+km_for_next_n_month
        # Initialize a LabelEncoder instance
        # Apply label encoding to columns in the DataFrame
        le = LabelEncoder()
        df[['Country']] = df[['Country']].apply(lambda col1: le.fit_transform(col1))
        df[['Tire_Company']] = df[['Tire_Company']].apply(lambda col2: le.fit_transform(col2))
        df[['Site_Name']] = df[['Site_Name']].apply(lambda col2: le.fit_transform(col2))
        df[['Vehicle_Asset_Number']] = df[['Vehicle_Asset_Number']].apply(lambda col4: le.fit_transform(col4))
        df[['Tire Model']] = df[['Tire Model']].apply(lambda col5: le.fit_transform(col5))
        df[['Tire_Asset_Number']] = df[['Tire_Asset_Number']].apply(lambda col6: le.fit_transform(col6))
        df[['Road_Condition']] = df[['Road_Condition']].apply(lambda col9: le.fit_transform(col9))   
        
        df['Km_driven'] = pd.to_numeric(df['Km_driven'], errors='coerce')
        df['Tire_Tread'] = pd.to_numeric(df['Tire_Tread'], errors='coerce')
        df['Tire Model'] = pd.to_numeric(df['Tire Model'], errors='coerce')
        # Prepare the features (X) and target (y) for regression prediction
        X=df.drop(['Tire_Tread'],axis=1)
        y=df['Tire_Tread']
        # Take the first row of features and update the 'Km_driven' value with the predicted kilometers
        X = X.iloc[:1,:].copy()
        X = X.reset_index()
        X = X.drop("index",axis=1)
        X.at[0,'Km_driven']= float("% .2f"% Predict_kms)
        # Load the saved regression model
        with open('model_multi_linear.pkl', 'rb') as model:
            model = pickle.load(model)
            predicted_Tread = model.predict(X)
            need_to_replace = True if predicted_Tread < ThresholdTread else False
            json_dump = json.dumps({'Predicted_tread':predicted_Tread ,'N_months':N_months,'Predict_kms':float("% .2f"% Predict_kms),'Need_to_replace':need_to_replace}, cls=NumpyEncoder)  
        result_prediction.append({str(val):json_dump})   
    return {
        'statusCode': 200,
        'body': result_prediction,
        'data': "Results"
    }


@app.route('/')
def main_methods():
    
    return render_template('App/index.html')

@app.route('/twoviewsinone')
def twoviewsinOne_methods():
    return "Ritik API"
    return render_template('tmass/index2 views.html')