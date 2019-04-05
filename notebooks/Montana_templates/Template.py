
# coding: utf-8

# In[1]:


import cgi
import os
import jinja2
import random
from random import randrange
from random import randint
from datetime import timedelta
import datetime


# In[2]:


os.makedirs('./templates/', exist_ok=True)
os.makedirs('./output_docs/', exist_ok=True)
template_dir = './templates/'
output_docs_dir = './output_docs/'
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))


# In[3]:


template = jinja_env.get_template('template_mt.txt')


# In[4]:


names = [
"AAHP-HIAA",
"Al Asher, Pierre, Administrator of SDRS",
"Al Asher, Pierre, Administrator, SDRS",
"Al Asher, Pierre, Dir. of State Retirement",
"Al Asher, Pierre, SDRS",
"Al Asher, SD Retirement System (SDRS)",
"Al Asher, SDRS",
"Al Fjeldheim, SDCCA",
"Al Gregg, Dakota Towing, Brookings",
"Al Grogg, Dakota Towing, Brookings",
"Al Schroeder, Assn of Towns and Townships",
"Al Thoreson, Edgemont Schools",
"Alan Hanks, City of Rapid City, RC",
"Alan Ruhlman, Human Resources Director, Aberdeen",
"Albert Van Overmeer, Lennox School District",
"Alfred Reuer, Walworth County Commissioner",
"Alice Christensen",
"Alice Claggett, Mayor, City of Mitchell",
"Alison Haugo, Elk Point, Valley Bank",
"Allen Aden, Pierre Chief of Police",
"Allen Aden, Pierre Police Chief",
"Allen E. Nord, MD., R. City",
"Allen Nord, MD, lobbyist, SD Association of Family Physicians, Rapid City",
"Amber L. Fischer, Brookings",
"Andrea Kannegieter, Huron CVB",
"Andy Gerlach, Department of Military &amp; Veterans Affairs",
"Andy Gerlach, Department of Military and Veterans Affairs",
"Andy Gerlach, Department of Military and Veterans Affairs,",
"Andy Gerlach, Department of Veterans and Military Affairs",
"Andy Gerlach, SD Department of Military and Veteran's Affairs",
"Andy MacRae, Philip Morris Inc.",
"Angela Ehlers, SD Assn of Conservation Districts",
"Angela Ehlers, SD Assn. Of Conservation District",
"Angela Ehlers, SD Assn. Of Conservation Districts",
"Angela Ehlers, lobbyist, SD Association of Conservation Districts",
"Angela Ehlers, lobbyist, SD Association of Conservation Districts, Pierre",
"Angella Van Scharael, Bureau of Finance &amp; Management",
"Angie King, Northern Hills CASA",
"Anisah David,Self, Bushnell",
"Anita Fuoss, Jones Co. Commissioners, Murdo",
"Ann Holzhauser (SD Department of Social Services)",
]

for numb in range(5): # output docs count can be changed here.
    session = random.choice(list(range(60, 66)))

    startdate = datetime.date(random.choice(list(range(2007, 2017))),1,1)
    date = startdate + datetime.timedelta(randint(1,365))
    date = date.strftime('%B %-d, %Y')

    rand_names = set()
    for r in range(randint(10,30)):
        rand_names.add(random.choice(names))
    rand_names = '\n'.join(rand_names)
    
    with open(output_docs_dir + 'mt_doc_' + str(numb) + '.txt', 'w') as o:
        o.write(template.render(session=session, date=date, names=rand_names))


# In[ ]:




