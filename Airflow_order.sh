#translate into airflow

#truncate the graphs 
python3 pre_scrape.py

#run scrapy
docker run --rm scrapy_project 

#start the janusgraph, scylladb will automatically start
docker start 7add8a6dc787

#create the janusgraph and update the tables
python3 post_scrape.py

#go into the conf/remote.yaml and serializer: { className: org.apache.tinkerpop.gremlin.driver.ser.GryoMessageSerializerV3d0, config: { serializeResultToString: true }}
#:remote connect tinkerpop.server conf/remote.yaml
#:remote console
#g
#docker exec -it --user root janusgraph-server /bin/bash
#apt-get update && apt-get install nano