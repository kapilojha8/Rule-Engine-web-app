# using flask_restful
from flask import Flask, jsonify, request
import json
import mysql.connector
import pandas as pd

from flask import  render_template

#for rule Engine 
import sys
from Loan_attributions import Actions, Class, Allocations, DataHandler
from Rule_model import Rule,Rule_Connection
import copy
from Rules_using_JSON import  Rules_using_JSON
from Rules_using_XML import RulesUsingXML
import pandas as pd
from datetime import datetime
from preprocessing_of_data import PreprocessingOfData
import secrets
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

@app.route("/submit-form",methods = ["POST"])
def Onsubmit():

    def Evaluate_and_take_decision(Rule_chain, Rule, Data_rule):
        Rule.evaluate(Data_rule)
        # if Rule.Is_Nested and (not Rule.Evaluated_result):
        #     Rule.Evaluated_result = Evaluate_and_take_decision(Rule_chain, Rule.Nested_Rule, Data_rule)
        return Rule_chain.take_decisions(Rule)

    if request.method == "POST":
        amount_financed = request.form.get('amount_financed')
        deposit_amount = request.form.get('deposit_amount')
        balloon_amount = request.form.get('balloon_amount')
        repayment_term_month = request.form.get('repayment_term_month')
        applicant_entity_type = request.form.get('applicant_entity_type')
        asset_supplier_type = request.form.get('asset_supplier_type')
        asset_category = request.form.get('asset_category')
        asset_type = request.form.get('asset_type')
        asset_manufacture_year = request.form.get('asset_manufacture_year')
        usage_type = request.form.get('usage_type')
        gst_registered_date = request.form.get('gst_registered_date')
        abn_registered_date = request.form.get('abn_registered_date')
        guarantor_1_residential_status = request.form.get('guarantor_1_residential_status')
        ClientData = {
        'application_number':[secrets.token_hex(8)],
        'amount_financed': [amount_financed],
        'deposit_amount': [deposit_amount],
        'balloon_amount': [balloon_amount],
        'repayment_term_month': [repayment_term_month],
        'applicant_entity_type': [applicant_entity_type],
        'asset_supplier_type': [asset_supplier_type],
        'asset_category': [asset_category],
        'asset_type': [asset_type],
        'asset_manufacture_year': [asset_manufacture_year],
        'usage_type': [usage_type],
        'gst_registered_date': [gst_registered_date],
        'abn_registered_date': [abn_registered_date],
        'guarantor_1_residential_status': [guarantor_1_residential_status]
    }
    Preprocessed_data = PreprocessingOfData(ClientData)
    Preprocessed_data.converting_df_to_dict()
    Data_of_Rule_test = Preprocessed_data.Data_of_Rule_test
    
    # Check for right usage:
    #   - approach = rule-engine
    #   - approach = if-statements

    

   
    Rules_by_Lender  = Rules_using_JSON('Rules.json')
    Rules_by_Lender.Create_rules_using_json()
    Remarks = Rules_by_Lender.Remarks
    

    Result_Evalulated = {"Pass":[],"Fail":[]}
    
    for Data_rule in Data_of_Rule_test:
        
        for LenderName,LenderRule in Rules_by_Lender.lender_rules.items():
            
            if LenderName.upper().find(Data_rule['asset_category'].split("_")[0].upper()) == -1:
                continue
            print("Hello")
            temppte = copy.deepcopy(LenderRule)
            remarks = ""
            Running_logs = ""
            while temppte!=None:
                
                Rule_evaluate = temppte.Rule.evaluate(Data_rule)
                Running_logs = Running_logs + " -- " + Rule_evaluate['Remark']  if Running_logs!="" else Rule_evaluate['Remark']
                EATD = temppte.take_decisions(temppte.Rule)
                if not EATD :
                    break
                # if type(temppte.Rule.Remark) == int:
                #     remarks +=  Remarks[f'{temppte.Rule.Remark}']
                temppte = temppte.next_Rule

            
            if temppte == None:
                LName = LenderName
                application_number = Data_rule['application_number']
                result = " Eligible"
                Result_Evalulated["Pass"].append([application_number,LName,result])
                Data_rule['Evaluated_Lender'] = LenderName
                print("This is tempte running Logs ",Running_logs)
            else:
                LName = LenderName
                application_number = Data_rule['application_number']
                result = " Not Eligible"
                print(f"Failure Remarks : {Rule_evaluate['Remark'].split('||')[-1]}")
                result_remark = Rule_evaluate['Remark'].split('||')[-1]
                Result_Evalulated["Fail"].append([application_number,LName,result,result_remark])
                Data_rule['Evaluated_Lender'] = "No Lender Found!"
                print("This is tempte running Logs ",Running_logs)

    
    return jsonify(Result_Evalulated)
    exit()