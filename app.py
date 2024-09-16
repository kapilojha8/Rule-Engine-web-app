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



@app.route('/')
def main_methods():

    return render_template('App/index.html')

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
        TempDict = {"Flexi":{},'Pepper':{},"Resimac":{}}
        for LenderName,LenderRule in Rules_by_Lender.lender_rules.items():
            
            # print("The Lender Name is :",LenderName)
            if LenderName.upper().find(Data_rule['asset_category'].split("_")[0]) == -1:
                continue
            
            if "Pepper" in LenderName:
                lender = 'Pepper'
                TempDict[lender][LenderName] = {}
            elif "Resimac" in LenderName:
                lender = 'Resimac'
                TempDict[lender][LenderName] = {}
            else :
                lender = 'Flexi'
                TempDict[lender][LenderName] = {}

            temppte = copy.deepcopy(LenderRule)
            remarks = ""
            Running_logs = ""
            while temppte!=None:
                Rule_evaluate = temppte.Rule.evaluate(Data_rule)
                Running_logs = Running_logs + " -- " + Rule_evaluate['Remark']  if Running_logs!="" else Rule_evaluate['Remark']
                # TempDict[LenderName] = {temppte.RC_ID:}
                TempDict[lender][LenderName][ temppte.RC_ID] = {}
                EATD = temppte.take_decisions(temppte.Rule)
                TempDict[lender][LenderName][temppte.RC_ID]["RC_Result"] = Rule_evaluate['Return_result']   # Rule Condition Result
                TempDict[lender][LenderName][temppte.RC_ID]["Remark"] = Rule_evaluate['Remark']
                if not EATD :
                    break
                if type(temppte.Rule.Remark) == int:
                    remarks +=  Remarks[f'{temppte.Rule.Remark}']
                temppte = temppte.next_Rule
    
            if temppte == None:
                TempDict[lender][LenderName]['Eligibility'] = True
                LName = LenderName
                application_number = Data_rule['application_number']
                result = " Eligible"
                Result_Evalulated["Pass"].append([application_number,LName,result])
                Data_rule['Evaluated_Lender'] = LenderName
                print("This is tempte running Logs ",Running_logs)
            
            else:
                TempDict[lender][LenderName]['Eligibility'] = False
                LName = LenderName
                application_number = Data_rule['application_number']
                result = " Not Eligible"
                print(f"Failure Remarks : {Rule_evaluate['Remark'].split('||')[-1]}")
                result_remark = Rule_evaluate['Remark'].split('||')[-1]
                Result_Evalulated["Fail"].append([application_number,LName,result,result_remark])
                Data_rule['Evaluated_Lender'] = "No Lender Found!"
                print("This is tempte running Logs ",Running_logs)
 

            
    for lender,lendername in TempDict.items():
        print("---->",lender)
        for i,j in lendername.items():
            print("---->",i)
            print(j)

    
    return jsonify(TempDict)
    exit()