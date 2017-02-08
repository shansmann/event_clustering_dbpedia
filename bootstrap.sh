echo "mkdir data"

cd data

if [ ! -f "data.json" ]
then
  curl 'https://dickesb.firebaseio.com/events/gridsearch.json' > data.json
fi

cd ..
cd src

echo "download finished"

clear

echo "starting module"

echo "starting preprocessing"
python3 preprocessing.py


echo "starting semantification"
python3 disambiguation.py


echo "start fuzzyfication"
python3 fuzzyfication.py


echo "starting kmeans"
echo "see kmeans ipynb for clustering"
