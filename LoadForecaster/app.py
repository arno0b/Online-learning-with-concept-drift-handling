from flask import Flask, render_template, jsonify, request
import base64
from io import BytesIO
from matplotlib.figure import Figure
import os
import pickle
from river import stream
from river import compose
from river import linear_model
from river import preprocessing
from river import metrics
from river import utils
from river import optim
from datetime import datetime, timedelta
from loaddb import init_db, save_data, get_last_hours_data, update_actual_value, datetime_exists

app = Flask(__name__)

model_path = './models/model.pkl'

db_uri = 'sqlite:///loaddb.db'  # Use the appropriate database URL for your RDBMS
db_session = init_db(db_uri)

@app.route('/')
def hello():
    return render_template('index.html', grpah=get_graph())


def get_ordinal_date(x):
    return {'ordinal_date': x['moment'].toordinal()}

def get_model():
    if os.path.isfile(model_path):
        print("existing model")
        with open(model_path, 'rb') as f:
            return pickle.load(f)
        
    return compose.Pipeline(
    ('ordinal_date', compose.FuncTransformer(get_ordinal_date)),
    ('scale', preprocessing.StandardScaler()),
    ('lin_reg', linear_model.LinearRegression(
        intercept_lr=0,
        optimizer=optim.SGD(0.03)
    ))
)

def save_model(model):
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

def get_graph():
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2])
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

@app.route("/train-model", methods=['POST'])
def train_model():
    metric1 = utils.Rolling(metrics.MSE(), 12)
    metric2 = utils.Rolling(metrics.MAE(), 12)
    input_json = request.get_json(force=True)
    x = {}
    x['moment'] = datetime.strptime(input_json['moment'], '%m/%d/%Y %H:%M')
    if not datetime_exists(db_session, x['moment']):
        y = float(input_json['gen'])
        model = get_model()
        y_pred = model.predict_one(x)
        model.learn_one(x, y)
        metric1.update(y, y_pred)
        metric2.update(y, y_pred)
        save_model(model)
        save_data(db_session, x['moment'], y, y_pred, metric2.get(), metric1.get())
        dictToReturn = {'prediction': y_pred, 'mse': metric1.get(), 'mae': metric2.get()}
        return jsonify(dictToReturn)
    return {"msg": "datetime exists"}
    

@app.route("/graph")
def graph():
    # Generate the figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2])
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

@app.route("/d3graph")
def d3_graph():
    return render_template("d3.html")

@app.route('/get_hourly_data')
def get_hourly_data():
    import random

    data = []
    db_data = get_last_hours_data(db_session)
    for d in db_data:
        data.append({
            'date': d.datetime.isoformat(),
            'actual': d.actual_value,
            'forecasted': d.forecasted_value,
            'mse': d.mse_value,
            'mae': d.mae_value
        })
    last_date = db_data[-1].datetime
    last_mse = db_data[-1].mse_value
    last_mae = db_data[-1].mae_value
    model = get_model()
    for i in range(12):
        data.append({
            'date': last_date.isoformat(),
            'actual': None,
            'forecasted': model.predict_one({"moment": last_date}),
            'mse': last_mse,
            'mae': last_mae
        })
        last_date += timedelta(hours=1)
         

    return jsonify(data)


# main driver function
if __name__ == '__main__':
 
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run(debug=True)