from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_cors import cross_origin
import pandas as pd
import socketio
import pickle

model = pickle.load(open('C:/Users/anura/Desktop/Anurag/Python Project/CODING_PRACTICE/flight_rf.pkl', 'rb'))