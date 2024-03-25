projects=("Lang" "Chart" "Closure" "Math" "Mockito" "Time")
for project in "${projects[@]}"
do
    echo "Save initial prompt............."$project""
    python3 main.py initial-save "$project" y
done
for project in "${projects[@]}"
do
    echo "Runing initial chat............."$project""
    python3 main.py initial-chat "$project" y
done
for project in "${projects[@]}"
do
    echo "Runing chatrepair............."$project""
    python3 main.py chatrepair "$project" y
done