from server import serve, restore_data
from middleware.middleware import setup_middleware

setup_middleware()
restore_data()
serve()
