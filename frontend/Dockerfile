# Nginx serves our static HTML/JS files
FROM nginx:alpine

# Copy our static files into Nginx's default serving directory
COPY src/ /usr/share/nginx/html/

# Replace the default Nginx config with ours
# (ours adds the /api proxy to the backend)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
