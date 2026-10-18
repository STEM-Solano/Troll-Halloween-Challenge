import asyncio
import pygame
import sys
import random
import os
from fractions import Fraction
pygame.init()
# iOS may not expose audio until the first user interaction.
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    AUDIO_AVAILABLE = True
except (pygame.error, OSError):
    AUDIO_AVAILABLE = False
SCREEN_WIDTH=800
SCREEN_HEIGHT=600
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("Trials and Trolls")
clock=pygame.time.Clock()
current_music=None
music_sounds={}
music_channel=pygame.mixer.Channel(0) if AUDIO_AVAILABLE else None
music_transition=None
encounter_transition=None
MUSIC_VOLUME=0.5
MUSIC_FADE_MS=1200
def play_enemy_music(enemy_number):
    global current_music,music_transition
    if not AUDIO_AVAILABLE:
        return
    filename=f"music/{enemy_number+1}.ogg"
    if current_music==filename and music_transition is None:
        return
    music_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),filename)
    try:
        if filename not in music_sounds:
            music_sounds[filename]=pygame.mixer.Sound(music_path)
        if music_transition:
            # Replace the queued track if the player reaches another fight mid-transition.
            music_transition["next_filename"]=filename
            if music_transition["phase"]=="in":
                music_transition={"phase":"out","next_filename":filename,"start_time":pygame.time.get_ticks(),"start_volume":music_channel.get_volume()}
                music_channel.fadeout(MUSIC_FADE_MS)
            return
        if current_music is None or not music_channel.get_busy():
            music_channel.stop()
            music_channel.set_volume(0)
            music_channel.play(music_sounds[filename],loops=-1)
            current_music=filename
            music_transition={"phase":"in","next_filename":filename,"start_time":pygame.time.get_ticks(),"start_volume":0}
        else:
            # Fade the current track completely out before starting the next one.
            music_transition={"phase":"out","next_filename":filename,"start_time":pygame.time.get_ticks(),"start_volume":music_channel.get_volume()}
            music_channel.fadeout(MUSIC_FADE_MS)
    except (pygame.error,OSError) as error:
        music_transition=None
        print(f"Could not play {filename}: {error}")
def update_music_transition():
    global current_music,music_transition
    if not AUDIO_AVAILABLE or not music_transition:
        return
    now=pygame.time.get_ticks()
    elapsed=now-music_transition["start_time"]
    progress=min(1,elapsed/MUSIC_FADE_MS)
    if music_transition["phase"]=="out":
        # No new track starts until the old one has fully faded away.
        if progress>=1:
            filename=music_transition["next_filename"]
            try:
                music_channel.stop()
                music_channel.set_volume(0)
                music_channel.play(music_sounds[filename],loops=-1)
                current_music=filename
                music_transition={"phase":"in","next_filename":filename,"start_time":now,"start_volume":0}
            except pygame.error as error:
                music_transition=None
                print(f"Could not start {filename}: {error}")
    elif music_transition["phase"]=="in":
        music_channel.set_volume(MUSIC_VOLUME*progress)
        if progress>=1:
            music_channel.set_volume(MUSIC_VOLUME)
            music_transition=None
def stop_music():
    global current_music,music_transition
    if music_channel is not None:
        music_channel.stop()
    current_music=None
    music_transition=None
WHITE=(255,255,255)
BLACK=(0,0,0)
RED=(220,50,50)
GREEN=(50,220,50)
BLUE=(50,100,220)
GRAY=(80,80,80)
YELLOW=(240,220,50)
PURPLE=(170,80,220)
font=pygame.font.Font(None,40)
small_font=pygame.font.Font(None,30)
large_font=pygame.font.Font(None,60)
ATTACK_NAMES={
    "Green Slime":["Bounced","Splashed","Body Slammed"],
    "Blue Slime":["Slapped","Splashed","Crushed"],
    "Fire Slime":["Burned","Scorched","Exploded"],
    "Magic Slime":["Spit Poison","Bit","Poison Burst"],
    "Minotaur Chief":["Charged","Gored","Crushed"],
    "Troll King":["Club Smash","Earthquake","Royal Slam"]
}
QUESTIONS={}
selected_grade=5
def make_answer_choices(answer):
    """Create exactly one mathematically correct numeric or symbolic choice."""
    answer_text=str(answer)
    choices=[answer_text]
    try:
        number=Fraction(answer_text)
        spread=max(2,int(abs(number)*Fraction(1,5)))
        values={number}
        attempts=0
        while len(choices)<4 and attempts<100:
            attempts+=1
            wrong=number+random.randint(-spread,spread)
            if wrong not in values:
                values.add(wrong)
                choices.append(str(wrong) if "/" in answer_text or wrong.denominator==1 else str(float(wrong)))
        offset=spread+1
        while len(choices)<4:
            wrong=number+offset
            offset+=1
            if wrong not in values:
                values.add(wrong)
                choices.append(str(wrong) if "/" in answer_text or wrong.denominator==1 else str(float(wrong)))
    except (ValueError,TypeError,ZeroDivisionError):
        # Current symbolic templates have nonconstant derivatives/integrals,
        # positive multiples of pi, or scientific notation >= 1000.
        # Constants avoid equivalent antiderivatives such as F(x) + C + 1.
        choices.extend(["0","1","-1"])
    random.shuffle(choices)
    return choices,choices.index(answer_text)
def generate_one_question(grade):
    """Generate a question from the selected grade's actual math curriculum."""
    def whole(low,high):
        return random.randint(low,high)
    if grade==1:
        a,b=whole(0,10),whole(0,10)
        if random.choice([True,False]):
            return f"What is {a} + {b}?",a+b
        a=whole(0,10); b=whole(0,a)
        return f"What is {a} - {b}?",a-b
    if grade==2:
        kind=random.choice(["add","subtract","multiply","place"])
        if kind=="add":
            a,b=whole(10,99),whole(1,99); return f"What is {a} + {b}?",a+b
        if kind=="subtract":
            a,b=whole(10,99),whole(1,99); a,b=max(a,b),min(a,b); return f"What is {a} - {b}?",a-b
        if kind=="multiply":
            a,b=whole(2,5),whole(2,10); return f"What is {a} × {b}?",a*b
        digit=whole(1,9); number=digit*10; return f"In {number}, what is the value of the {digit} in the tens place?",number
    if grade==3:
        kind=random.choice(["multiply","divide","fraction","round"])
        if kind=="multiply":
            a,b=whole(2,12),whole(2,12); return f"What is {a} × {b}?",a*b
        if kind=="divide":
            b=whole(2,12); q=whole(2,12); return f"What is {b*q} ÷ {b}?",q
        if kind=="fraction":
            d=random.choice([2,3,4,5,6,8]); n=whole(1,d-1); return f"What fraction of {d} equal parts is {n} part(s)?",f"{n}/{d}"
        n=whole(10,999); return f"Round {n} to the nearest ten.",((n+5)//10)*10
    if grade==4:
        kind=random.choice(["multiply","divide","fraction","perimeter","decimal"])
        if kind=="multiply":
            a,b=whole(12,99),whole(2,9); return f"What is {a} × {b}?",a*b
        if kind=="divide":
            b=whole(2,12); q=whole(10,99); return f"What is {b*q} ÷ {b}?",q
        if kind=="fraction":
            d=random.choice([4,6,8,10,12]); n=whole(1,d-1); return f"Simplify {n*2}/{d*2}.",str(Fraction(n,d))
        if kind=="perimeter":
            a,b=whole(2,20),whole(2,20); return f"A rectangle is {a} cm by {b} cm. What is its perimeter?",2*(a+b)
        a,b=whole(1,9),whole(1,9); return f"What is {a/10:.1f} + {b/10:.1f}?",f"{(a+b)/10:.1f}"
    if grade==5:
        kind=random.choice(["fraction","decimal","percent","area","order"])
        if kind=="fraction":
            d=random.choice([2,3,4,5,6,8,10]); n=whole(1,d-1); return f"What is {n}/{d} + {d-n}/{d}?",1
        if kind=="decimal":
            a,b=whole(10,999)/100,whole(10,999)/100; return f"What is {a:.2f} + {b:.2f}?",f"{a+b:.2f}"
        if kind=="percent":
            pct=random.choice([10,20,25,50,75]); n=random.choice([20,40,60,80,100,200]); return f"What is {pct}% of {n}?",pct*n//100
        if kind=="area":
            a,b=whole(2,20),whole(2,20); return f"A rectangle is {a} by {b}. What is its area?",a*b
        return f"What is 6 + 3 × 4?",18
    if grade==6:
        kind=random.choice(["fraction","negative","ratio","decimal","expression"])
        if kind=="fraction":
            d=random.choice([2,3,4,5,6,8,10]); n=whole(1,d-1); return f"What is {n}/{d} + {d-n}/{d}?",1
        if kind=="negative":
            a,b=whole(-15,15),whole(-15,15); op=random.choice(["+","-"]); ans=a+b if op=="+" else a-b; return f"What is {a} {op} ({b})?",ans
        if kind=="ratio":
            a,b,k=whole(1,6),whole(1,6),whole(2,8); return f"A ratio is {a}:{b}. If both parts are multiplied by {k}, what is the new second part?",b*k
        if kind=="decimal":
            a,b=whole(10,999)/10,whole(10,999)/10; return f"What is {a:.1f} - {b:.1f}?",f"{a-b:.1f}"
        x=whole(1,15); b=whole(1,20); return f"If x = {x}, what is 3x + {b}?",3*x+b
    if grade==7:
        kind=random.choice(["proportion","percent","integer","equation","probability"])
        if kind=="proportion":
            a,b,k=whole(2,12),whole(2,12),whole(2,10); return f"If {a}/{b} = x/{b*k}, what is x?",a*k
        if kind=="percent":
            pct=random.choice([5,10,15,20,25,30,40,50]); n=whole(2,20)*10; return f"What is {pct}% of {n}?",pct*n/100
        if kind=="integer":
            a,b=whole(-30,30),whole(-30,30); return f"What is ({a}) × ({b})?",a*b
        if kind=="equation":
            x=whole(-10,20); b=whole(-10,20); return f"Solve: x + ({b}) = {x+b}",x
        a,b=whole(1,6),whole(2,10); return f"A bag has {a} red and {b} blue marbles. What is P(red)?",f"{a}/{a+b}"
    if grade==8:
        kind=random.choice(["linear","exponent","slope","pythagorean","scientific"])
        if kind=="linear":
            x=whole(-10,15); a=whole(2,8); b=whole(-15,15); return f"Solve: {a}x + ({b}) = {a*x+b}",x
        if kind=="exponent":
            a=whole(2,6); b=whole(2,4); return f"What is {a}^{b}?",a**b
        if kind=="slope":
            x1,y1,x2,y2=whole(-5,5),whole(-5,5),whole(1,8),whole(1,8); x2+=x1; y2+=y1; dx=x2-x1; dy=y2-y1; from math import gcd; g=gcd(abs(dy),abs(dx)); return f"Find the slope through ({x1}, {y1}) and ({x2}, {y2}).",f"{dy//g}/{dx//g}" if dx else 0
        if kind=="pythagorean":
            a,b=random.choice([(3,4),(5,12),(8,15),(6,8)]); return f"A right triangle has legs {a} and {b}. Find the hypotenuse.",int((a*a+b*b)**0.5)
        a=whole(1,9); return f"Write {a*1000} in scientific notation.",f"{a} × 10^3"
    if grade==9:
        kind=random.choice(["equation","slope","system","polynomial","function"])
        if kind=="equation":
            x=whole(-10,15); a=whole(2,8); b=whole(-20,20); return f"Solve: {a}x + {b} = {a*x+b}",x
        if kind=="slope":
            m=whole(-8,8); b=whole(-10,10); return f"For y = {m}x + {b}, what is the slope?",m
        if kind=="system":
            x,y=whole(-5,8),whole(-5,8); return f"Solve the system: x + y = {x+y}; x - y = {x-y}. What is x?",x
        if kind=="polynomial":
            a,b=whole(1,8),whole(1,8); return f"Expand (x + {a})(x + {b}). What is the constant term?",a*b
        x=whole(-5,5); return f"If f(x) = 2x² + 1, find f({x}).",2*x*x+1
    if grade==10:
        kind=random.choice(["quadratic","radical","geometry","trig","function"])
        if kind=="quadratic":
            r1,r2=whole(-6,6),whole(-6,6); return f"For x² - ({r1+r2})x + ({r1*r2}) = 0, what is the sum of the roots?",r1+r2
        if kind=="radical":
            n=whole(2,15); return f"Simplify √{n*n}.",n
        if kind=="geometry":
            r=whole(2,10); return f"What is the area of a circle with radius {r}? (Use π.)",f"{r*r}π"
        if kind=="trig":
            return random.choice([( "What is sin(30°)?","1/2"),("What is cos(60°)?","1/2"),("What is tan(45°)?","1")])
        x=whole(-5,5); return f"If f(x) = x² - 3, find f({x}).",x*x-3
    if grade==11:
        kind=random.choice(["log","trig","sequence","complex","function"])
        if kind=="log":
            base=random.choice([2,3,10]); power=whole(1,5); return f"Evaluate log base {base} of {base**power}.",power
        if kind=="trig":
            return random.choice([("What is sin(90°)?","1"),("What is cos(0°)?","1"),("What is sin(0°)?","0"),("What is cos(180°)?","-1")])
        if kind=="sequence":
            a,d=whole(-10,20),whole(2,8); return f"An arithmetic sequence starts {a}, {a+d}, {a+2*d}. What is the 10th term?",a+9*d
        if kind=="complex":
            a,b=whole(1,8),whole(1,8); return f"What is ({a} + {b}i) + ({a} - {b}i)?",2*a
        x=whole(-5,5); return f"If f(x) = 3x² - 2x, find f({x}).",3*x*x-2*x
    # Grade 12: limits, derivatives, integrals, advanced algebra and calculus.
    kind=random.choice(["derivative","power_rule","integral","limit","logarithm","complex"])
    if kind=="derivative":
        a=whole(1,8); n=whole(2,6); return f"If f(x) = {a}x^{n}, what is f'(x)?",f"{a*n}x^{n-1}"
    if kind=="power_rule":
        a=whole(1,6); n=whole(2,5); return f"Differentiate {a}x^{n}.",f"{a*n}x^{n-1}"
    if kind=="integral":
        a=whole(1,8); n=whole(1,5); return f"Find ∫ {a}x^{n} dx.",f"{a}/{n+1}x^{n+1} + C"
    if kind=="limit":
        a=whole(1,8); return f"Evaluate lim (x→{a}) of (x² - {a*a})/(x - {a}).",2*a
    if kind=="logarithm":
        power=whole(1,5); return f"Evaluate log₁₀(10^{power}).",power
    a,b=whole(1,8),whole(1,8); return f"What is ({a}+{b}i)({a}-{b}i)?",a*a+b*b
def generate_question_bank(difficulty,subject):
    # Attack choice changes the question pool, while the selected grade sets the curriculum.
    bank=[]
    seen=set()
    attempts=0
    while len(bank)<15 and attempts<1000:
        attempts+=1
        text,answer=generate_one_question(selected_grade)
        if text in seen:
            continue
        seen.add(text)
        choices,correct_index=make_answer_choices(answer)
        bank.append((text,choices,correct_index))
    return bank
def get_questions(difficulty,subject):
    grade_key=str(selected_grade)
    if grade_key not in QUESTIONS:
        QUESTIONS[grade_key]={}
    if difficulty not in QUESTIONS[grade_key]:
        QUESTIONS[grade_key][difficulty]={}
    if subject not in QUESTIONS[grade_key][difficulty]:
        QUESTIONS[grade_key][difficulty][subject]=generate_question_bank(difficulty,subject)
    return QUESTIONS[grade_key][difficulty][subject]
class Button:
    def __init__(self,x,y,width,height,text):
        self.rect=pygame.Rect(x,y,width,height)
        self.text=text
    def draw(self,cooldown=0):
        color=GRAY if cooldown>0 else BLUE
        display_text=f"{self.text}\n{cooldown}" if cooldown>0 else self.text
        pygame.draw.rect(screen,color,self.rect)
        pygame.draw.rect(screen,WHITE,self.rect,3)
        lines=display_text.split("\n")
        start_y=self.rect.centery-(len(lines)*25)//2
        for i,line in enumerate(lines):
            text=small_font.render(line,True,WHITE)
            rect=text.get_rect(center=(self.rect.centerx,start_y+i*25))
            screen.blit(text,rect)
    def clicked(self,event):
        # The event loop normalizes both finger and mouse events into
        # MOUSEBUTTONDOWN with coordinates in the 800x600 game surface.
        return (event.type == pygame.MOUSEBUTTONDOWN
                and getattr(event, "button", None) == 1
                and self.rect.collidepoint(event.pos))

class Character:
    def __init__(self,hp,strength,defense,image):
        self.max_hp=hp
        self.hp=hp
        self.strength=strength
        self.defense=defense
        self.image=image
        self.level=1
        self.experience=0
        self.experience_needed=100
        self.alive=True
        self.mastery={"addition":0,"multiplication":0,"division":0,"algebra":0,"patterns":0}
        self.correct=0
        self.wrong=0
    def attack(self,enemy,attack_name,bonus=1):
        damage_values={"Swing":35,"Spin":50,"Smash":70,"Headbutt":17}
        damage=damage_values[attack_name]
        final_damage=max(1,int(damage*self.strength/enemy.defense*bonus))
        enemy.hp=max(0,enemy.hp-final_damage)
        return final_damage
    def check_alive(self):
        if self.hp<=0:
            self.alive=False
class Enemy:
    def __init__(self,name,hp,strength,defense,xp,weak,medium,strong,image,subject):
        self.name=name
        self.max_hp=hp
        self.hp=hp
        self.strength=strength
        self.defense=defense
        self.experience_given=xp
        self.image=image
        self.weak_attack=weak
        self.medium_attack=medium
        self.strong_attack=strong
        self.subject=subject
        self.alive=True
    def attack(self,player):
        damage=random.choice([self.weak_attack,self.medium_attack,self.strong_attack])
        final_damage=max(1,damage*self.strength//player.defense)
        player.hp=max(0,player.hp-final_damage)
        return final_damage
    def check_alive(self):
        if self.hp<=0:
            self.alive=False
def load_image(path):
    try:
        return pygame.image.load(path).convert_alpha()
    except:
        surface=pygame.Surface((120,120))
        surface.fill(GRAY)
        return surface
player=Character(120,2,2,load_image("images/Knight(192).png"))
encounter=0
def make_enemy(number):
    enemies=[
        Enemy("Green Slime",100,2,3,100,4,8,12,load_image("images/Green Slime.png"),"addition"),
        Enemy("Blue Slime",140,3,4,150,6,12,18,load_image("images/Blue Slime.png"),"multiplication"),
        Enemy("Fire Slime",170,3,4,180,7,12,18,load_image("images/Fire Slime.png"),"division"),
        Enemy("Magic Slime",210,4,5,220,8,15,22,load_image("images/Magic Slime.png"),"algebra"),
        Enemy("Minotaur Chief",240,4,5,350,8,15,22,load_image("images/Minotaur Chief(175).png"),"patterns"),
        Enemy("Troll King",350,5,6,700,10,20,28,load_image("images/Troll King(175).png"),"algebra")
    ]
    return enemies[number]
slime=make_enemy(encounter)
title_play_button=Button(300,445,200,60,"Play")
grade_down_button=Button(160,280,80,55,"-")
grade_up_button=Button(560,280,80,55,"+")
intro_continue_button=Button(300,450,200,60,"Continue")
victory_continue_button=Button(300,400,200,60,"Continue")
restart_button=Button(300,450,200,60,"Restart")
swing_button=Button(50,470,150,60,"Swing")
spin_button=Button(220,470,150,60,"Spin")
smash_button=Button(390,470,150,60,"Smash")
headbutt_button=Button(560,470,170,60,"Headbutt")
heal_button=Button(50,400,150,60,"Heal")
answer_buttons=[Button(80,350,280,70,""),Button(440,350,280,70,""),Button(80,440,280,70,""),Button(440,440,280,70,"")]
hp_button=Button(100,470,180,60,"HP +60")
strength_button=Button(310,470,180,60,"Strength +2")
defense_button=Button(520,470,180,60,"Defense +2")
game_state="TITLE"
battle_over=False
winner=""
message="Choose an attack!"
level_message=""
question=None
question_choices=[]
question_answer=0
question_subject=""
selected_attack=""
question_message=""
question_locked=False
question_start_time=0
QUESTION_TIME_LIMIT=10
attack_cooldowns={"Swing":0,"Spin":0,"Smash":0,"Headbutt":0,"Heal":0}
def draw_text(text,x,y,color=WHITE,size="normal"):
    if size=="large":
        surface=large_font.render(text,True,color)
    elif size=="small":
        surface=small_font.render(text,True,color)
    else:
        surface=font.render(text,True,color)
    screen.blit(surface,(x,y))
def draw_centered_text(text,center_x,center_y,color=WHITE,size="normal"):
    if size=="large":
        selected_font=large_font
    elif size=="small":
        selected_font=small_font
    else:
        selected_font=font
    surface=selected_font.render(text,True,color)
    rect=surface.get_rect(center=(center_x,center_y))
    screen.blit(surface,rect)
def draw_hp_bar(x,y,current_hp,max_hp,color):
    width=250
    height=25
    pygame.draw.rect(screen,GRAY,(x,y,width,height))
    health=int(width*max(0,current_hp)/max_hp)
    pygame.draw.rect(screen,color,(x,y,health,height))
    pygame.draw.rect(screen,WHITE,(x,y,width,height),3)
def draw_health():
    draw_text("PLAYER",50,20)
    draw_hp_bar(50,55,player.hp,player.max_hp,GREEN)
    draw_text(f"{player.hp}/{player.max_hp}",130,90,size="small")
    draw_text(f"LV {player.level}",50,125,YELLOW,"small")
    draw_text(slime.name.upper(),470,20,RED)
    draw_hp_bar(500,55,slime.hp,slime.max_hp,RED)
    draw_text(f"{slime.hp}/{slime.max_hp}",580,90,size="small")
def draw_title():
    screen.fill(BLACK)
    draw_centered_text("TRIALS AND TROLLS",400,100,RED,"large")
    draw_centered_text("Choose your math grade",400,205,YELLOW)
    grade_down_button.draw()
    grade_up_button.draw()
    draw_centered_text(f"GRADE {selected_grade}",400,307,GREEN,"large")
    draw_centered_text("Each grade has its own math topics and difficulty.",400,365,WHITE,"small")
    draw_centered_text("Grade 1: basic math  |  Grade 12: calculus",400,395,WHITE,"small")
    draw_centered_text("Choose a grade, then press Play!",400,425,WHITE,"small")
    title_play_button.draw()
def draw_intro():
    screen.fill(BLACK)
    draw_text("Trials and Trolls",250,50,RED,"large")
    lines=[
        "Win by defeating all 6 enemies, ending with the Troll King.",
        "Choose an attack; answer within 10 seconds to deal damage.",
        "Correct? You attack first. If the enemy survives, it hits back!",
        "Wrong or late? Your attack fails; the enemy still hits you.",
        "Heal restores up to 25% of max HP, then the enemy attacks.",
        "After Heal, land a correct attack to make Heal ready again.",
        "Defeating an enemy restores 60 HP; there is no final hit back.",
        "Level-up upgrades refill HP. At 0 HP, you lose. Heal early!"
    ]
    y=130
    for line in lines:
        draw_text(line,55,y,size="small")
        y+=36
    intro_continue_button.draw()
def draw_battle():
    screen.fill(BLACK)
    draw_health()
    screen.blit(player.image,(150,250))
    screen.blit(slime.image,(550,150))
    draw_text(f"{slime.name} blocks your path!",180,150,YELLOW)
    lines=message.split("\n")[-3:]
    y=190
    for line in lines:
        draw_text(line,80,y,size="small")
        y+=35
    if not battle_over:
        swing_button.draw(attack_cooldowns["Swing"])
        spin_button.draw(attack_cooldowns["Spin"])
        smash_button.draw(attack_cooldowns["Smash"])
        headbutt_button.draw(attack_cooldowns["Headbutt"])
        heal_button.draw(attack_cooldowns["Heal"])
        draw_text("Normal",82,535,YELLOW,"small")
        draw_text("Hard",270,535,YELLOW,"small")
        draw_text("Very Hard",418,535,YELLOW,"small")
        draw_text("Easy",620,535,YELLOW,"small")
    elif winner=="PLAYER":
        draw_text("VICTORY!",300,350,GREEN)
        victory_continue_button.draw()
def draw_question():
    screen.fill(BLACK)
    draw_text("KNOWLEDGE TRIAL",235,40,PURPLE,"large")
    draw_text(f"GRADE {selected_grade} MATH TRIAL",255,105,YELLOW,"small")
    draw_text(f"Attack: {selected_attack}",300,135,WHITE,"small")
    elapsed=(pygame.time.get_ticks()-question_start_time)/1000
    remaining=max(0,QUESTION_TIME_LIMIT-elapsed)
    timer_color=RED if remaining<=3 else YELLOW
    draw_text(f"TIME: {remaining:.1f}",330,165,timer_color,"small")
    draw_text(question,100,205)
    draw_text("Correct: you attack first. Surviving enemies hit back!",100,265,GREEN,"small")
    for i,button in enumerate(answer_buttons):
        button.text=question_choices[i]
        button.draw()
    if question_message:
        draw_text(question_message,180,540,YELLOW,"small")
def draw_levelup():
    screen.fill(BLACK)
    draw_text("LEVEL UP!",280,50,YELLOW,"large")
    draw_text(level_message,120,130)
    draw_text(f"Level: {player.level}",100,190,WHITE,"small")
    draw_text(f"HP: {player.max_hp}",100,225,GREEN,"small")
    draw_text(f"Strength: {player.strength}",300,225,RED,"small")
    draw_text(f"Defense: {player.defense}",500,225,BLUE,"small")
    draw_text("Choose your upgrade:",270,320,WHITE,"small")
    hp_button.draw()
    strength_button.draw()
    defense_button.draw()
def draw_gameover():
    screen.fill(BLACK)
    if encounter>=6:
        draw_text("YOU DEFEATED THE TROLL KING!",120,120,GREEN,"large")
        draw_text("You mastered the trials.",230,220,YELLOW)
        draw_text(f"Questions correct: {player.correct}",230,290)
        draw_text(f"Questions wrong: {player.wrong}",230,330)
    else:
        draw_text("GAME OVER",250,150,RED,"large")
        draw_text(f"Questions correct: {player.correct}",230,250)
        draw_text(f"Questions wrong: {player.wrong}",230,290)
    restart_button.draw()
def reset_cooldowns():
    for attack in attack_cooldowns:
        attack_cooldowns[attack]=0
def reduce_cooldowns():
    for attack in attack_cooldowns:
        if attack_cooldowns[attack]>0:
            attack_cooldowns[attack]-=1
def level_up():
    global level_message
    leveled=False
    while player.experience>=player.experience_needed:
        player.experience-=player.experience_needed
        player.level+=1
        player.experience_needed*=2
        leveled=True
    if leveled:
        level_message=f"You reached level {player.level}!"
    return leveled
def get_question_difficulty(attack):
    if attack=="Headbutt":
        return "easy"
    if attack=="Swing":
        return "normal"
    if attack=="Spin":
        return "hard"
    if attack=="Smash":
        return "very_hard"
def create_question(subject,attack):
    global question,question_choices,question_answer,question_subject,question_message,question_locked,question_start_time
    question_subject=subject
    difficulty=get_question_difficulty(attack)
    question,choices,correct_index=random.choice(get_questions(difficulty,subject))
    correct_answer=choices[correct_index]
    question_choices=choices.copy()
    random.shuffle(question_choices)
    question_answer=question_choices.index(correct_answer)
    question_message=""
    question_locked=False
    question_start_time=pygame.time.get_ticks()
def start_attack(move):
    global selected_attack,game_state
    if attack_cooldowns[move]>0:
        return
    selected_attack=move
    create_question(slime.subject,move)
    game_state="QUESTION"
def enemy_counterattack():
    global message,battle_over,winner,game_state
    enemy_damage=slime.attack(player)
    attack_name=random.choice(ATTACK_NAMES[slime.name])
    message+=f"\n{slime.name} used {attack_name} and dealt {enemy_damage} damage!"
    player.check_alive()
    if not player.alive:
        battle_over=True
        winner="SLIME"
        game_state="GAMEOVER"
        message=f"The {slime.name} defeated you..."
def question_time_expired():
    return (pygame.time.get_ticks()-question_start_time)>=QUESTION_TIME_LIMIT*1000
def answer_question(index):
    global question_message,question_locked,game_state,message
    if question_locked:
        return
    if question_time_expired():
        question_locked=True
        player.wrong+=1
        player.mastery[question_subject]=max(0,player.mastery[question_subject]-1)
        question_message="TIME'S UP! Your attack failed!"
        message=f"You ran out of time on your {selected_attack}!"
        enemy_counterattack()
        if game_state!="GAMEOVER":
            game_state="BATTLE"
        return
    question_locked=True
    if index==question_answer:
        player.correct+=1
        player.mastery[question_subject]+=1
        question_message="CORRECT! Attack successful!"
        perform_attack(selected_attack)
    else:
        player.wrong+=1
        player.mastery[question_subject]=max(0,player.mastery[question_subject]-1)
        question_message="WRONG! Your attack failed!"
        message=f"You missed your {selected_attack}!"
        enemy_counterattack()
    if game_state!="GAMEOVER":
        game_state="BATTLE"
def perform_attack(move):
    global message,battle_over,winner,encounter
    damage=player.attack(slime,move,1.5)
    message=f"You used {move} and dealt {damage} damage!"
    cooldowns={"Swing":2,"Spin":3,"Smash":5,"Headbutt":0}
    attack_cooldowns[move]=cooldowns[move]
    reduce_cooldowns()
    slime.check_alive()
    if not slime.alive:
        player.experience+=slime.experience_given
        player.hp=min(player.max_hp,player.hp+60)
        battle_over=True
        winner="PLAYER"
        message+=f"\nYou defeated the {slime.name}!"
        message+="\nYou recovered 60 HP!"
        encounter+=1
        return
    enemy_counterattack()
def player_heal():
    global message
    if attack_cooldowns["Heal"]>0:
        message="Heal is on cooldown!"
        return
    heal_amount=int(player.max_hp/4)
    old_hp=player.hp
    player.hp=min(player.max_hp,player.hp+heal_amount)
    healed=player.hp-old_hp
    attack_cooldowns["Heal"]=2
    reduce_cooldowns()
    message=f"You healed for {healed} HP!"
    enemy_counterattack()
def next_enemy():
    global encounter_transition
    if encounter>=6:
        global game_state
        game_state="GAMEOVER"
        return
    # Fade the current soundtrack and the current screen to black together.
    encounter_transition={"phase":"out","start_time":pygame.time.get_ticks()}
def load_next_enemy():
    global slime,battle_over,winner,message,game_state,current_music,music_transition
    if encounter>=6:
        game_state="GAMEOVER"
        return
    # The old track is fully stopped before the new encounter and track begin.
    if music_channel is not None:
        music_channel.stop()
        music_channel.set_volume(0)
    current_music=None
    music_transition=None
    slime=make_enemy(encounter)
    play_enemy_music(encounter)
    battle_over=False
    winner=""
    reset_cooldowns()
    message=f"A {slime.name} appears!"
    game_state="BATTLE"
def update_encounter_transition():
    global encounter_transition
    if encounter_transition is None:
        return
    now=pygame.time.get_ticks()
    progress=min(1,(now-encounter_transition["start_time"])/MUSIC_FADE_MS)
    if encounter_transition["phase"]=="out":
        # Screen and soundtrack fade out over the same 1.2-second interval.
        if music_channel is not None and music_channel.get_busy():
            music_channel.set_volume(MUSIC_VOLUME*(1-progress))
        if progress>=1:
            if music_channel is not None:
                music_channel.stop()
            load_next_enemy()
            encounter_transition={"phase":"in","start_time":now}
    elif encounter_transition["phase"]=="in" and progress>=1:
        encounter_transition=None
def draw_encounter_fade():
    if encounter_transition is None:
        return
    now=pygame.time.get_ticks()
    progress=min(1,(now-encounter_transition["start_time"])/MUSIC_FADE_MS)
    alpha=int(255*progress) if encounter_transition["phase"]=="out" else int(255*(1-progress))
    overlay=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    overlay.fill(BLACK)
    overlay.set_alpha(alpha)
    screen.blit(overlay,(0,0))
def restart_game():
    global player,slime,encounter,battle_over,winner,message,game_state,QUESTIONS
    stop_music()
    player=Character(120,2,2,load_image("images/Knight(192).png"))
    encounter=0
    slime=make_enemy(encounter)
    battle_over=False
    winner=""
    message="Choose an attack!"
    reset_cooldowns()
    QUESTIONS={}
    game_state="TITLE"
# Mobile input adapter. Safari/Pygbag may deliver FINGERDOWN, FINGERUP,
# MOUSEBUTTONDOWN, or a synthetic mouse event for the same physical tap.
# Convert each physical tap into one game-space mouse click.
_last_pointer_ms = -10000
_last_pointer_pos = (-1000, -1000)
_touch_debug = None

def mobile_click_event(event):
    global _last_pointer_ms, _last_pointer_pos, _touch_debug
    is_finger = event.type in (pygame.FINGERDOWN, pygame.FINGERUP)
    is_mouse = event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", 0) == 1
    if not (is_finger or is_mouse):
        return None

    if is_finger:
        # SDL finger coordinates are normalized from 0 to 1.
        x = round(event.x * SCREEN_WIDTH)
        y = round(event.y * SCREEN_HEIGHT)
    else:
        x, y = event.pos
        # Normally pygame already maps browser coordinates to its canvas.
        # Account for a differently sized display surface if one is used.
        actual_width, actual_height = screen.get_size()
        if (actual_width, actual_height) != (SCREEN_WIDTH, SCREEN_HEIGHT):
            x = round(x * SCREEN_WIDTH / actual_width)
            y = round(y * SCREEN_HEIGHT / actual_height)

    now = pygame.time.get_ticks()
    # Ignore synthesized duplicate mouse events and the finger-up following
    # a finger-down, but allow rapid taps at different button positions.
    if (now - _last_pointer_ms < 350 and
            abs(x - _last_pointer_pos[0]) < 32 and
            abs(y - _last_pointer_pos[1]) < 32):
        return None
    _last_pointer_ms = now
    _last_pointer_pos = (x, y)
    _touch_debug = (x, y, now)
    print(f"Input: {'finger' if is_finger else 'mouse'} at ({x}, {y}) state={game_state}")
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (x, y)})

async def main():
    global game_state, selected_grade, message
    running=True
    while running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
                continue
            if encounter_transition is not None:
                continue
            event = mobile_click_event(event)
            if event is None:
                continue
            if game_state=="TITLE":
                if grade_down_button.clicked(event):
                    selected_grade=max(1,selected_grade-1)
                elif grade_up_button.clicked(event):
                    selected_grade=min(12,selected_grade+1)
                elif title_play_button.clicked(event):
                    game_state="INTRO"
            elif game_state=="INTRO":
                if intro_continue_button.clicked(event):
                    play_enemy_music(encounter)
                    game_state="BATTLE"
                    message="Choose an attack!"
            elif game_state=="BATTLE":
                if not battle_over:
                    if swing_button.clicked(event):
                        start_attack("Swing")
                    elif spin_button.clicked(event):
                        start_attack("Spin")
                    elif smash_button.clicked(event):
                        start_attack("Smash")
                    elif headbutt_button.clicked(event):
                        start_attack("Headbutt")
                    elif heal_button.clicked(event):
                        player_heal()
                elif winner=="PLAYER":
                    if victory_continue_button.clicked(event):
                        if encounter>=6:
                            game_state="GAMEOVER"
                        elif level_up():
                            game_state="LEVELUP"
                        else:
                            next_enemy()
            elif game_state=="QUESTION":
                if not question_locked:
                    for i,button in enumerate(answer_buttons):
                        if button.clicked(event):
                            answer_question(i)
            elif game_state=="LEVELUP":
                if hp_button.clicked(event):
                    player.max_hp+=60
                    player.hp=player.max_hp
                    next_enemy()
                elif strength_button.clicked(event):
                    player.strength+=2
                    player.hp=player.max_hp
                    next_enemy()
                elif defense_button.clicked(event):
                    player.defense+=2
                    player.hp=player.max_hp
                    next_enemy()
            elif game_state=="GAMEOVER":
                if restart_button.clicked(event):
                    restart_game()
        if game_state=="QUESTION" and not question_locked and question_time_expired():
            answer_question(-1)
        update_music_transition()
        update_encounter_transition()
        if game_state=="TITLE":
            draw_title()
        elif game_state=="INTRO":
            draw_intro()
        elif game_state=="BATTLE":
            draw_battle()
        elif game_state=="QUESTION":
            draw_question()
        elif game_state=="LEVELUP":
            draw_levelup()
        elif game_state=="GAMEOVER":
            draw_gameover()
        draw_encounter_fade()
        # Small temporary marker: green = tap reached Python game code.
        if _touch_debug is not None:
            tx, ty, tap_time = _touch_debug
            if pygame.time.get_ticks() - tap_time < 650:
                pygame.draw.circle(screen, (50, 255, 100), (tx, ty), 9, 2)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
    pygame.quit()
    # Return cleanly instead of exiting the browser interpreter.

asyncio.run(main())
