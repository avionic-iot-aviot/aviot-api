from app import create_app

# TODO variabile l'ambiente
application = create_app('development')

if __name__ == '__main__':
    application.run(
        host='0.0.0.0'
        #ssl_context=('certs/flask/cert.pem', 'certs/flask/key.pem')
    )
