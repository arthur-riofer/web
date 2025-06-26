import pandas as pd
from hdbcli import dbapi
import firebase_admin
from firebase_admin import credentials, firestore
from cryptography.fernet import Fernet

def obter_dados_do_sap():
    cred=credentials.Certificate("riofer-537b0-firebase-adminsdk-buo66-13151ce8e2.json")
    firebase_admin.initialize_app(cred)
    db=firestore.client()
    key=open("secret.key","rb").read()
    f=Fernet(key)
    doc=db.collection("configuracoes").document("conexao").get().to_dict()
    dec={k:f.decrypt(v.encode()).decode() for k,v in doc.items()}
    conn=dbapi.connect(
        address=dec['host'],port=int(dec['port']),
        user=dec['Usuário'],password=dec['Senha']
    )
    cur=conn.cursor()
    cur.execute("SELECT * FROM SBO_RIOFER.RIOFER_MRP_BEAS")
    cols=["MrpTipo","ItemCode","ItemName","MRP","Estoque",
          "EstoqueMax","EstoqueMin","DispPkl","Desenvolvimento",
          "Comprimento","Espessura","Planejado"]
    df=pd.DataFrame(cur.fetchall(),columns=cols)
    cur.close();conn.close()
    return df