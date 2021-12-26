# Author : Ajinkya Gorad
# Date : 23-26 Dec, 2021

# Based on plotly Dash interface for plotting in html https://dash.plotly.com/
# Binance python library  https://python-binance.readthedocs.io from Binance API https://binance-docs.github.io


# issues : slow, may overrequest should be converted to websocket api for smooth realtime updates
from binance.client import Client
from binance.enums import *
from matplotlib import pyplot as plt
import datetime
from matplotlib.animation import FuncAnimation
import pandas as pd
import IPython 
import pytz
import numpy as np
from config import api_key,api_secret

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd



client = Client(api_key, api_secret)
futures_symbols=pd.DataFrame(client.futures_exchange_info()['symbols']).symbol.values

app = dash.Dash(__name__,external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.scripts.config.serve_locally = False
app.layout = html.Div([html.H4(children='Exchange Info'),
                       dcc.Dropdown(id='currency-pair-dropdown',
                                   options=[{'label':x,'value':x} for x in futures_symbols],value='BTCUSDT'),
                       html.Div([
                       html.Div([html.H3('Candlestick chart 🕯 📈 📉'),dcc.Graph(id='klines')],
                                className="four columns"), 
                       html.Div([html.H3('Ongoing trades ⚖️'),dcc.Graph(id='trades')],
                                 className="four columns"), 
                       html.Div([html.H3('Order book 📙 '),dcc.Graph(id='order-book')],
                                 className="four columns")],
                           className="row"),
                       dcc.Interval(id='interval-component',interval=1*500,n_intervals=0)])

@app.callback([Output('klines','figure')],[Input('interval-component','n_intervals'),Input('currency-pair-dropdown','value')])
def update_klines(n,sym):
    df=pd.DataFrame(client.get_klines(symbol=sym,interval=Client.KLINE_INTERVAL_1MINUTE))
    df.columns = ['opentime','open','high','low','close','volume','closetime','quote_asset_volume','number_of_trades','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','to_be_ignored']
    df['opentime'] = [datetime.datetime.fromtimestamp(x/1000.0) for x in df.opentime]
    fig=go.Figure(data=[go.Candlestick(x=df['opentime'],
                                               open=df['open'],
                                               high=df['high'],
                                               low = df['low'],
                                               close = df['close'])])
    fig.update_layout(title=sym, yaxis_title='value',width=500,height=500)
    fig.update_layout(hoverdistance=0)
    return [fig]

@app.callback([Output('trades','figure')],
              [Input('interval-component','n_intervals'),
               Input('currency-pair-dropdown','value')])
def update_trade_price_chart(n,sym):
    trades = client.get_recent_trades(symbol=sym,limit=500)
    trades = pd.DataFrame(trades)
    trades['time'] = [datetime.datetime.fromtimestamp(x/1000.0) for x in trades.time]
    trades['price']=trades['price'].astype(float)
    trades['qty'] = trades['qty'].astype(float)
    fig= px.scatter(trades,x='time',y='price',size='qty',color='qty')
    fig.update_layout(title=sym, yaxis_title='value',width=500,height=500)
    fig.update_layout(hoverdistance=0)
    return [fig]

@app.callback([Output('order-book','figure')],
              [Input('interval-component','n_intervals'),
               Input('currency-pair-dropdown','value')])
def update_order_book(n,sym):
    depth = client.get_order_book(symbol=sym,limit=1000)
    bids_df=pd.DataFrame(depth['bids'],columns=['price','qty'])
    bids_df['type']='bids'
    asks_df=pd.DataFrame(depth['asks'],columns=['price','qty'])
    asks_df['type']='asks'
    bids_df=bids_df.append(asks_df)
    bids_df['price'] = bids_df['price'].astype(float)
    bids_df['qty'] = bids_df['qty'].astype(float)
    #asks_df['price'] = asks_df['price'].astype(float)
    #asks_df['qty'] = asks_df['qty'].astype(float)
    
    fig=px.line(bids_df,x='qty',y='price',color='type',color_discrete_map={'bids':'green','asks':'red'})
    #fig.add_trace(px.bar(asks_df,x='price',y='qty',marker_color='type'))
    fig.update_layout(title=sym+' Order Book', yaxis_title='Qty',width=500,height=500)
    fig.update_layout(xaxis_range=[0,15])
    #fig.update_layout(yaxis_range=[50200,50400])
    return [fig]

    


if __name__ == '__main__':
    app.run_server(debug=True)
            