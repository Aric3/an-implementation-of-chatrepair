projects=("Lang" "Chart" "Closure" "Math" "Mockito" "Time")
for project in "${projects[@]}"
do
    echo "Runing initial chat............."$project""
    python3 main.py initial-chat "$project" n
done