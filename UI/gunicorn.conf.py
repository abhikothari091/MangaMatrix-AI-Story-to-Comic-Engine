# gunicorn.conf.py

# Increase the timeout to prevent worker timeouts on long requests
timeout = 180  # seconds (default is 30)

# Number of worker processes (adjust based on your plan)
workers = 1

# Number of threads per worker (to handle concurrent requests better)
threads = 2

# Bind to all interfaces on the default Render port
bind = "0.0.0.0:10000"

# Optional: log level for debugging (can be "info", "warning", "error")
loglevel = "info"
