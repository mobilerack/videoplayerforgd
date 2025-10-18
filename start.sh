#!/usr/bin/env bash

# A Streamlit indítása a Render által megkövetelt porton és címen
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
