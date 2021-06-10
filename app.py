from flask import Flask, render_template, flash, request, redirect
import pandas as pd
import numpy as np
import os
import csv
import cryptography
from cryptography.fernet import Fernet, InvalidToken

# Configure Flask app
app = Flask(__name__)
 
# Set secret key for Flask environment
app.config['SECRET_KEY'] = "A_secret_key"

# Ensure web templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# define function to clean unwanted symbol 
def clean_symbols(cell):
    # define unwanted characters
    unwanted_characters = ['"', ',', '-', '+']
    # strip the unwanted character
    for character in unwanted_characters:
        if character in str(cell):
            cell = cell.replace(character,'')          
    return cell

# define function to check for NULL
def check_missing_data(cell):
    if (cell == 'nan') or (cell == 'Info not found in database') or (cell == 'Null') or (cell == 'No Data'):
        return None
    else:
        return cell

# define function to check if values are fully integer, eg. for Mobile No. and IC No. 
# Also check if it contains certain string like '12345' or '678910'
def check_digit_validity(cell):
    if cell == None:
        return
    else:
        if '12345' in str(cell):
            return None
        if '678910' in str(cell):
            return None
        if str(cell).isnumeric():
            return cell
        else: 
            return None

# Create function for encryption 
def Encrypt_Data(cell):
    # Generate random key
    key = Fernet.generate_key()

    # convert str to bytes with encode
    message = str(cell).encode()
    f = Fernet(key)
    Encrypted_Message = f.encrypt(message)

    # Store key to a separate file
    file = open('key.key', 'wb')
    file.write(key)
    file.close()

    return Encrypted_Message

# Define Decryption function (if needed)
def Decrypt_Data(cell):
    # Reading key from a specific file
    file = open('key.key', 'rb')
    key = file.read()
    file.close
    
    f = Fernet(key)
    # This function assumes the cells are encrypted. 
    Decrypted_Message = f.decrypt(cell)

    return Decrypted_Message

# Define clean, encrypt and delete function
def Clean_and_Encrypt(path, file_name, file_name_path):

    # open current CSV with pandas Dataframe
    df = pd.read_csv(file_name_path)

    # Apply relevant functions to cells that need cleaning. Here are global functions that can be applied to the whole CSV 
    for column in df.columns:
        df[column] = df[column].apply(clean_symbols)    
        df[column] = df[column].apply(check_missing_data)

    # Apply functions to cell that is Column specific
    df['Mobile No.'] = df['Mobile No.'].apply(check_digit_validity) 
    df['IC No.'] = df['IC No.'].apply(check_digit_validity) 
    df['Business Unit ID'] = df['Business Unit ID'].apply(check_digit_validity) 

    # Remove rows with NULL. 
    # NOTE: I decide to only remove rows with NULL in ALL columns, because sample_data has too little rows
    df = df.dropna(how = 'all') 

    # To cast the data type as per recommended  
    df = df.astype({'Name': str, 'Mobile No.': str, 'IC No.':str, 'Race': str}) # NULL will be converted to string too, hence recommended to all lines with NULL actually. 
    df['Business Unit ID'] = df['Business Unit ID'].astype(dtype = int, errors = 'ignore') # ignore errors because I did not remove all NULL values in this test

    # Remove duplicate rows
    df = df.drop_duplicates(keep = 'first')

    # Export to CSV as file_name_Output.csv
    Output_directory = os.path.dirname(path) + '/dir_B'
    file_name= file_name.replace('.csv','')
    Output_file_path = Output_directory + '/' + file_name + '_Output.csv'
    print(Output_file_path)
    df.to_csv(Output_file_path)

    # Apply encryption function to columns we want
    df['Name'] = df['Name'].apply(Encrypt_Data) 
    df['Mobile No.'] = df['Mobile No.'].apply(Encrypt_Data) 
    df['IC No.'] = df['IC No.'].apply(Encrypt_Data) 

    # Export encrypted CSV to a separate directory
    Output_directory = os.path.dirname(path) + '/dir_C'
    file_name= file_name.replace('.csv','')
    Encrypted_Output_file_path = Output_directory + '/' + file_name + '_Output_Encrypted.csv'
    print(Encrypted_Output_file_path)
    df.to_csv(Encrypted_Output_file_path)

    # delete current CSV file
    os.remove(file_name_path)


@app.route("/", methods = ["GET", "POST"])
# This is the main function. Web server will run once a directory input is received via POST
def main():
    if request.method == 'POST':
        # Input the path to search        
        path = request.form.get('directory')

        # The extension you want to detect
        extension = '.csv'

        # Search through the files in the directory
        for root, dirs_list, files_list in os.walk(path):
            for file_name in files_list:
                if os.path.splitext(file_name)[1] == extension:
                    file_name_path = os.path.join(root, file_name)
                    print (file_name_path)   # This is the full path of target csv file
                    Clean_and_Encrypt (path, file_name, file_name_path)
                    
        flash('Files Successfully Cleaned!')

        return redirect ("/")

    else: 
        return render_template('Input_dir.html')



