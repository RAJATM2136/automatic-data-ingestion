#!/usr/bin/env python
# coding: utf-8

# In[1]:


import snowflake.connector
import pandavro as pdx
import configparser
from cryptography.fernet import Fernet

#getting config files

config = configparser.ConfigParser()
config.read('SnowflakeExtractionFramework.ini')

#fernet key used to encrypt passwords in config files
fernet_key='VlUVeecxDDQTIsdD3fK4J1yuNr0QsPO0kBGU-6yEZxQ='.encode()

def config_decrypt(encoded):
    key = fernet_key
    fernet = Fernet(key)
    encoded=encoded[2:len(encoded)-1]
    return fernet.decrypt(encoded.encode()).decode()

#getting details of view or table to be downloaded
view_sql = config['extract']['sql']
table_name = config['extract']['table']
file_format = config['extract']['doc_type']

def to_xml(df):
    def row_xml(row):
        xml = ['<row>']
        for i, col_name in enumerate(row.index):
            xml.append('  <{0}>{1}</{0}>'.format(col_name, row.iloc[i]))
        xml.append('</row>')
        return '\n'.join(xml)
    res = '\n'.join(df.apply(row_xml, axis=1))
    return(res)

con = snowflake.connector.connect(
    user=config['snowflake']['user'],
    password=config_decrypt(config['snowflake']['password']),
    account=config['snowflake']['account']
)

cs = con.cursor()

cs.execute('USE warehouse '+config['snowflake']['warehouse'])
cs.execute('USE database '+config['snowflake']['database'])
cs.execute('USE ROLE '+config['snowflake']['role'])


def extract(sql,table,doc_type):
    if(sql==''):
        sql='select * from '+table
    else:
        table=config['extract']['view_name']
    cs.execute(sql)
    df_snowflake = cs.fetch_pandas_all()
    file_location = config['extract']['file_location']+table+'.'+doc_type
    if(doc_type=='csv'):
        df_snowflake.to_csv(file_location,index=False)
    elif(doc_type=='json'):
        df_snowflake.to_json(path_or_buf=file_location,orient ='records')
    elif(doc_type=='avro'):
         pdx.to_avro(file_location, df_snowflake)
    elif(doc_type=='parquet'):
        df_snowflake.to_parquet(file_location)
    elif(doc_type=='xml'):
        xml_df=to_xml(df_snowflake)
        with open(file_location, 'w') as f:
            f.write(to_xml(df_snowflake))


extract(sql=view_sql,table=table_name,doc_type=file_format)


# In[ ]:




