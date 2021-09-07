from managev_app import app

if __name__ == "__main__":
    # managev_app.run(debug=True, port=8080)
    app.run(host="0.0.0.0", debug=True, port=8080)
