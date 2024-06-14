## create db
- created a cloud sql postgres 15 db
  - private IP (just created default network while going through wizard)
  - named it `kyoshi-dev`

## install gcloud
you just download tarball, extract it, then run install.sh
https://cloud.google.com/sdk/docs/install

## deploy docker image
- created `docker` repo in artifact registry
```
gcloud auth login --update-adc
gcloud auth configure-docker us-docker.pkg.dev

docker buildx build  --platform linux/amd64 -t us-docker.pkg.dev/kyoshi-dev/kyoshi/kyoshi-api:dev .
docker image push us-docker.pkg.dev/kyoshi-dev/kyoshi/kyoshi-api:dev


docker buildx build  --platform linux/amd64 -t us-docker.pkg.dev/kyoshi-prd/kyoshi/kyoshi-api:prd .
docker image push us-docker.pkg.dev/kyoshi-prd/kyoshi/kyoshi-api:prd
```

## connect to cloud sql
install cloud-sql-proxy https://cloud.google.com/sql/docs/mysql/connect-auth-proxy#mac-m1
```
# check connection name
gcloud sql instances describe kyoshi-dev --format='value(connectionName)'

./cloud-sql-proxy kyoshi-dev:us-central1:kyoshi-dev
./cloud-sql-proxy kyoshi-prd:us-central1:kyoshi-prd
```
For now, use the public ip. You can enable it in Cloud SQL Console > Connections > Network.
Later, maybe setup a VM or you shoudl be able to create a VPN in GCP. Then use wireguard or something to connect to it.
But if you have public ip and no authorized networks, you still need cloud-sql-proxy to connect, so that's probably fine.

Update password in alembic.ini and then run `alembic upgrade head`

## cloud run
create session secret: `openssl rand -base64 16`

## connect cloud run to cloud sql
https://cloud.google.com/sql/docs/postgres/connect-run

## make cloud public
https://cloud.google.com/blog/topics/developers-practitioners/how-create-public-cloud-run-services-when-domain-restricted-sharing-enforced
(configure both index & 404 page to point to index.html)
- allows react-router to do the routing
- otherwise gcs will look for an actual web page called /chat or whatever

## add a load balancer to map domain name to cloud run
https://cloud.google.com/load-balancing/docs/https/setup-global-ext-https-serverless
  
## frontend (hosting a static website)
```
# set the src/config.ts `API_BASE_URL = "https://dev-api.goginko.com"`
npm run build
gsutil cp -r dist/* gs://kyoshi-web-dev
```
https://cloud.google.com/storage/docs/hosting-static-website
organization policies: temporarily override to make bucket public

note: certificates take 24 hours to generate
  certificate will only work if the domain you put there directs to your lb
  so don't add random domains
follow instructions exactly!
need to use premium tier network (or else can only connect from one region)


## google sign in
OAuth 2.0 clients for web apps must use redirect URIs and JavaScript origins that are compliant with Google’s validation rules, including using the HTTPS scheme. 
https://developers.google.com/identity/protocols/oauth2/policies#secure-response-handling
