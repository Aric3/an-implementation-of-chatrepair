projects=("Lang" "Chart" "Closure" "Math" "Mockito" "Time")
for project in "${projects[@]}"
do
    echo "Runing chatrepair............."$project""
    python3 main.py chatrepair "$project" y
done