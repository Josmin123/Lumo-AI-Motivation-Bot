from dotenv import load_dotenv
import json
import os
from datetime import datetime

load_dotenv()

DATA_PATH=os.getenv("DATA_PATH","./data")
CONFIG_PATH=os.path.join(DATA_PATH,"user_config.json")

def ask_input(prompt, default=None):
    value = input(f"{prompt} " + (f"[{default}]: " if default else ": "))
    return value.strip() or default

def step_user_name():
    name = ask_input("👋 Hi! What’s your name?")
    return name
 
def step_focus_areas():
    print("\n What would you like Lumo to help you with?")
    options = [
        "Staying productive",
        "Emotional reflection",
        "Health and habits",
        "Managing goals",
        "Daily journaling",
        "Learning new things"
    ]

    selected = []
    for i, option in enumerate(options, 1):
        response = ask_input(f"{i}. {option}? (y/n)", default="n")
        if response.lower() == "y":
            selected.append(option)
    return selected

def step_personal_goals():
    print("\n Let's set a few personal goals you'd like Lumo to help you track.")
    try:
        count = int(os.getenv("DEFAULT_GOAL_COUNT", 3))
    except:
        count=3

    goals=[]

    for i in range(1,count+1):
        goal=ask_input(f"Goal {i}")  
        if goal:
            goals.append(goal)  

    return goals

def step_generate_folders(focus_areas):
    print("\n Creating folders based on your focus area...")

    #base mapping:focus area -> folder names
    folder_map={
        "Staying productive":["tasks","notes"],
        "Emotional reflection":["journal"],
        "Health and habits" : ["logs","habits"],
        "Managing goals" : ['goals'],
        "Daily journaling":['journal'],
        "Learning new things" :['notes','references']
    }

    created=set()

    for area in focus_areas:
        folders=folder_map.get(area,[])
        for folder in folders:
            folder_path=os.path.join(DATA_PATH,folder)
            os.makedirs(folder_path,exist_ok=True)
            created.add(folder)

    print(f"Folder created: {', '.join(sorted(created))}")        


def run_setup():
    print("\n Welcome to Lumo Setup")
    os.makedirs(DATA_PATH,exist_ok=True)

    #step1 :Name
    name=step_user_name()

    #step 2 Focus Areas
    focus_areas=step_focus_areas()

    #step 3: Goals
    goals = step_personal_goals()
    
    # Step 4: Create folders
    step_generate_folders(focus_areas)
    

    #save config
    config={
        "name":name,
        "focus_areas":focus_areas,
        "goals":goals
    }
  
    with open(CONFIG_PATH,"w") as f:
        json.dump(config,f,indent=2)

    #save just goals to a dedicated file
    goals_path=os.path.join(DATA_PATH,"goals.json")    
    with open(goals_path,"w") as f:
        json.dump(goals,f,indent=2)

    step_generate_starter_files(name, goals)    

    print(f"\n Setup complete! Welcome, {name}") 
    print(f"Your config is saved in {CONFIG_PATH}")  
    print(f"Your goals are saved in {goals_path}") 

def step_generate_starter_files(name,goals):
    today=datetime.now().strftime("%Y-%m-%d")

    #startee journal entry
    journal_path=os.path.join(DATA_PATH,"journal",f"{today}.md")
    with open(journal_path,"w") as f:
        f.write(f"# Daily Reflection -{today} \n\n")
        f.write(f"Hi {name},\n\n")
        f.write("## How do you feel today?\n\n")
        f.write("## What did you accomplish?\n\n")
        f.write("## Are you making progress toward your goals?\n")
        f.write("-" + "\n-".join(goals) + "\n\n")
        f.write("## Anything you wnat to reflect on?\n")

    # Starter Task File
    task_path = os.path.join(DATA_PATH, "tasks", "today.json")
    with open(task_path, "w") as f:
        json.dump({"tasks": []}, f, indent=2)

    #starter goals markdown
    goal_md_path=os.path.join(DATA_PATH,"goals","goals.md")  
    with open(goal_md_path,"w") as f:
        f.write("# Your Current Goals\n\n")  
        for goal in goals:
            f.write(f"-[ ] {goal}\n")

    print(f"starter journal created: {journal_path}") 
    print(f"Today's task list ready: {task_path}")  
    print(f"Goal Summary: {goal_md_path}")     






if __name__=="__main__" :
     run_setup()
     
