#!/usr/bin/env python
# coding: utf-8

# In[1]:


import geopandas as gpd
import population as ppl
import pandas as pd
import random
import bisect
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.special import ndtr
import numpy as np
import timeit

# # Lectura y preparción de datos

# In[2]:


blocks = pd.read_csv('data/Censo2017_Manzanas.csv', encoding='utf-8', sep=';')
blocks = blocks[blocks['COMUNA'] == 2101]
frame_viviendas=pd.read_csv("data/viviendas_antofagasta.csv", encoding='utf-8',sep=',',index_col=0)
people = pd.read_csv('data/personas_antofagasta.csv', encoding='utf-8')
fram_households=pd.read_csv("data/hogares_antofagasta.csv", encoding='utf-8',sep=',',index_col=0)
shape_manzana=gpd.read_file('data/MANZANA_IND_C17.shp')


# # Función probabilidades etarias/sexo y de tamaños de hogar para zona
def Size_household(id_zona,frame_viviendas):
    frame_viviendas=frame_viviendas.loc[frame_viviendas['ID_ZONA_LOC']==id_zona]
    sizes_householding=list(frame_viviendas['CANT_PER'])
    sizes_householding.remove(0)
    x1 = np.array(sizes_householding)
    x_eval = np.linspace(1, 10, num=10)
    size_household_cdf = ndtr(np.subtract.outer(x_eval, x1)).mean(axis=1)
    return(size_household_cdf)

def Prob_sex_age(id_zona,blocks,people):
    zone = id_zona
    zone_blocks = blocks[blocks['ID_ZONA_LOC'] == zone]
    zone_people = people[people['ID_ZONA_LOC'] == zone]

    def categorize_age(age):
       if age <= 5:
           return 'EDAD_0A5'
       elif 6 <= age <= 14:
           return 'EDAD_6A14'
       elif 15 <= age <= 64:
           return 'EDAD_15A64'
       else:
           return 'EDAD_65YMAS'

    zone_people['age_range'] = zone_people['P09'].apply(categorize_age)
    zone_counts = zone_people.pivot_table(index='P08', columns='age_range', values='Unnamed: 0', aggfunc='count').fillna(0)
    zone_probs = zone_counts / zone_counts.sum().sum()
    zone_probs = zone_probs[['EDAD_0A5', 'EDAD_6A14','EDAD_15A64','EDAD_65YMAS']]
    age_sex_cdf=[]
    i,j,cum=0,0,0
    for i in range(len(zone_probs.values)):
        for j in zone_probs.columns:
            cum+=zone_probs[j][i+1]
            age_sex_cdf.append(cum)
    return(age_sex_cdf,zone_probs)


# # Función generadora de tamaños de hogar y personas
def Size_generator(size_household_cdf,type_household):
    if type_household==1:
        size=0   
    elif type_household==3:
        size=1
    else:
        while True:
            n=random.uniform(0, 1)
            intervals = size_household_cdf
            size=bisect.bisect_left(intervals, n)
            if size>=2:
                break
    return(size+1)

def Age_sex_generator(age_sex_cdf):
    n=random.uniform(0, 1)
    if 0<=n<age_sex_cdf[0]:
        sex=1
        age_min=0
        age_max=5
    elif age_sex_cdf[0]<=n<age_sex_cdf[1]:
        sex=1
        age_min=6
        age_max=14
    elif age_sex_cdf[1]<=n<age_sex_cdf[2]:
        sex=1
        age_min=15
        age_max=64
    elif age_sex_cdf[2]<=n<age_sex_cdf[3]:
        sex=1
        age_min=65
        age_max=150
    elif age_sex_cdf[3]<=n<age_sex_cdf[4]:
        sex=2
        age_min=0
        age_max=5
    elif age_sex_cdf[4]<=n<age_sex_cdf[5]:
        sex=2
        age_min=6
        age_max=14
    elif age_sex_cdf[5]<=n<age_sex_cdf[6]:
        sex=2
        age_min=15
        age_max=64
    elif age_sex_cdf[6]<=n<age_sex_cdf[7]:
        sex=2
        age_min=65
        age_max=150
                    
    return(sex,age_min,age_max)


# # Buscador persona

def Search_person(sex,age_min,age_max,persons):
    position=0
    for x in persons:
        if x.sex == sex and age_min<=x.age and x.age<=age_max:
            person_id=x.person_id   
            break
        else:
            person_id = None
        position+=1    

    return(person_id,position,x)

def Search_person_2(age_min,age_max,persons):
    position=0
    for x in persons:
        if age_min<=x.age and x.age<=age_max:
            person_id=x.person_id   
            break
        else:
            person_id = None
        position+=1    

    return(person_id,position,x)

def Search_head_household(persons):
    position=0
    for x in persons:
        if 25<=x.age and x.age<=69:
            person_id=x.person_id   
            break
        else:
            person_id = None
        position+=1    
    return(person_id,position,x)


def Search_couple(person_id,persons_in_block,persons):
    for x in persons:
        if x.person_id==person_id:
            sex=x.sex
            age=x.age
            break
    if sex==1:
        sex_couple=2
    else:
        sex_couple=1
    position=0    
    for x in persons_in_block:
        if x.sex==sex_couple and x.age>=(age-7) and x.age<=(age+7):
            couple_id=x.person_id
            couple_age=x.age
            couple_sex=x.sex
            break
        else:
            couple_id=None
            x=None
        position+=1    
    return(couple_id,position,x)        


# # Genera cantidad de personas por rango etario en block

#PArece que esto no es necesario y esta de mas
def persons_for_agerange(blocks,id_block):
    persons_for_agerange=[]
    range_names=["EDAD_0A5","EDAD_6A14","EDAD_15A64","EDAD_65YMAS"]
    for i in range_names:
        persons_for_agerange.append(blocks.loc[blocks['ID_MANZENT']==id_block][i].item())
    for i in range(len(persons_for_agerange)):
        try:
            persons_for_agerange[i]=int(persons_for_agerange[i])
        except:
            pass
    return(persons_for_agerange)


# # Genera personas por block

def persons_for_block(persons_2,id_block,zone_probs,blocks,persons):
    number_of_persons=blocks.loc[blocks['ID_MANZENT']==id_block]['PERSONAS'].item()  #Obtengo cuanta gente realmente hay en el block
    range_names=["EDAD_0A5","EDAD_6A14","EDAD_15A64","EDAD_65YMAS"] 
    persons_in_block=[]   
    for i in range_names:
        if i=="EDAD_0A5":
            age_min,age_max=0,5
        elif i=="EDAD_6A14":
            age_min,age_max=6,14
        elif i=="EDAD_15A64":
            age_min,age_max=15,64
        elif i=="EDAD_65YMAS":
            age_min,age_max=65,150   
        number=blocks.loc[blocks['ID_MANZENT']==id_block][i].item()
        try:  #Si el numero de personas en el rango es diferente a * el try va a funcionar y se van a sacar la cantidad de personas dichas
            number=int(number)
            print("NUMBER: ",number)
            for j in range(number):
                person_id,position,x=Search_person_2(age_min,age_max,persons_2)
                persons_in_block.append(x)
                del persons_2[position]     
        except: #En caso de que sea * se va a generar un número de personas de forma probabilistica segun el cdf de la zona.
            number=int(sum(list(zone_probs[i]))*number_of_persons)
            print("NUMBER: ",number)
            for j in range(number):
                person_id,position,x=Search_person_2(age_min,age_max,persons_2)
                persons_in_block.append(x)
                del persons_2[position]
    return(persons_in_block)


# # Agregador de personas

def select_person(function,age_min,age_max,persons_in_block,block_households):
    if function=="Search_person_2":
        global person_id
        person_id,position,member=Search_person_2(age_min,age_max,persons_in_block) #Busco jefe de hogar
    elif function=="Search_couple":
        person_id,position,member=Search_couple(person_id,persons_in_block,persons)
    print("position= ",position)
    print("person_id= ",person_id)
    print("member= ", member)
    if person_id==None:
        print("NO HAY PERSONA ENTRE ",age_min," Y ",age_max)
    else:    
        block_households[i].add_member(member) #lo agrego al objeto hogar
    del persons_in_block[position]  #lo saco del conjunto de personas por asignar


# # Función Creadora de hogares en manzana (SIN USAR)

def create_household_block(num_household,block_households,persons_in_block,size_household_cdf):
    for i in range(num_household):
        print("\n INICIO CASA NUEVA")
        print("person in block= ",persons_in_block)    
        print("iterador i: ",i)    
        type_household=block_households[i].type
        print("tipo de casa: ",type_household)
        if type_household==1: #Hogar de una sola personas
            try:
                select_person("Search_person_2",27,69,persons_in_block,block_households) #Función para buscar una persona
            except:
                pass
        elif type_household==3: #hogar de una pareja
            try:
                select_person("Search_person_2",27,69,persons_in_block,block_households)
                select_person("Search_couple",27,69,persons_in_block,block_households)#Funcion para buscar una pareja de la persona anterior
            except:
                pass
        elif type_household==2: #Hogar de un padre con hijos
            size_household=Size_generator(size_household_cdf,2)-1 #Genero un tamaño de hogar
            print("Tamaño del hogar: ",size_household)
            try:
                select_person("Search_person_2",27,69,persons_in_block,block_households)
            except:
                pass
            for j in range(size_household-1): 
                try:
                    select_person("Search_person_2",0,26,persons_in_block,block_households) #Busco hijos para la persona
                except:
                    pass
        else:     #Hogar de multiples personas
            size_household=Size_generator(size_household_cdf,2)-1 #Genero un tamaño de hogar
            print("Tamaño del hogar: ",size_household)
            ages=[(28,69),(28,69),(0,18),(0,18),(19,27),(70,150),(28,69),(0,27),(0,27),(70,150)] #Será el orden en que se agrega la gente
            for j in range(size_household): #Voy agregando personas 
                try:
                    print("AGREGO PERSONA NUEVA EDAD ENTRE ",ages[j])
                    if j==0:
                        select_person("Search_person_2",ages[j][0],ages[j][1],persons_in_block,block_households)
                    if j==1:
                        select_person("Search_couple",ages[j][0],ages[j][1],persons_in_block,block_households)
                    else:
                        select_person("Search_person_2",ages[j][0],ages[j][1],persons_in_block,block_households)   
                except:
                    pass
        print("personas en la casa= ",block_households[i].members)       


# # MAIN

start = timeit.timeit()


id_zona=13833 #Para el testeo solamente, este debe ser iterado luego


#Genero todas las personas de la zona
zone_people = people[people['ID_ZONA_LOC'] == id_zona]
persons = []
for index, row in zone_people.iterrows():
    persons.append(ppl.Person(row['P09'], row['P08'], row['P07'], row['P15'], row['P18']))
persons_2=persons.copy() 

#Genero todos los hogares en la zona
zone_household=fram_households[fram_households['ID_ZONA_LOC']==id_zona]
households = []
for index, row in zone_household.iterrows():
    households.append(ppl.Household(row['TIPO_HOGAR']))
households_2=households.copy()    

#Genero el cdf de los tamaños de hogar, sexo y edad en la zona
size_household_cdf=Size_household(id_zona,frame_viviendas)
age_sex_cdf,zone_probs=Prob_sex_age(id_zona,blocks,people)


block=list(blocks.loc[blocks['ID_ZONA_LOC']==id_zona]['ID_MANZENT'])
block=block[1]



#Genero conjunto de personas que existen la manzana
persons_in_block=persons_for_block(persons_2,block,zone_probs,blocks,persons)


#Genero hogare en la manzana
num_household=int(blocks.loc[blocks['ID_MANZENT']==2101011001010]['CANT_HOG'])
block_households=[]
for i in range(num_household):
    block_households.append(households_2.pop(random.randint(0,len(households_2)-1)))
for x in block_households:
    x.add_block_id(2101011001010)


#Comienzo una iteración por cada hogar de una manzana
print("numero de casas= ",num_household)
# create_household_block(num_household,block_households,persons_in_block,size_household_cdf)
for i in range(num_household):
    print("\n INICIO CASA NUEVA")
    print("person in block= ",persons_in_block)    
    print("iterador i: ",i)    
    type_household=block_households[i].type
    print("tipo de casa: ",type_household)
    if type_household==1: #Hogar de una sola personas
        try:
            select_person("Search_person_2",27,69,persons_in_block,block_households) #Función para buscar una persona
        except:
            pass
    elif type_household==3: #hogar de una pareja
        try:
            select_person("Search_person_2",27,69,persons_in_block,block_households)
            select_person("Search_couple",27,69,persons_in_block,block_households)#Funcion para buscar una pareja de la persona anterior
        except:
            pass
    elif type_household==2: #Hogar de un padre con hijos
        size_household=Size_generator(size_household_cdf,2)-1 #Genero un tamaño de hogar
        print("Tamaño del hogar: ",size_household)
        try:
            select_person("Search_person_2",27,69,persons_in_block,block_households)
        except:
            pass
        for j in range(size_household-1): 
            try:
                select_person("Search_person_2",0,26,persons_in_block,block_households) #Busco hijos para la persona
            except:
                pass
    else:     #Hogar de multiples personas
        size_household=Size_generator(size_household_cdf,2)-1 #Genero un tamaño de hogar
        print("Tamaño del hogar: ",size_household)
        ages=[(28,69),(28,69),(0,18),(0,18),(19,27),(70,150),(28,69),(0,27),(0,27),(70,150)] #Será el orden en que se agrega la gente
        for j in range(size_household): #Voy agregando personas 
            try:
                print("AGREGO PERSONA NUEVA EDAD ENTRE ",ages[j])
                if j==0:
                    select_person("Search_person_2",ages[j][0],ages[j][1],persons_in_block,block_households)
                if j==1:
                    select_person("Search_couple",ages[j][0],ages[j][1],persons_in_block,block_households)
                else:
                    select_person("Search_person_2",ages[j][0],ages[j][1],persons_in_block,block_households)   
            except:
                pass
    print("personas en la casa= ",block_households[i].members)  
print("\n person in block SOBRANTES= ",persons_in_block)  

#Reviso si hay gente clonada
import collections
lista=[]
for i in range(len(block_households)):
    for x in block_households[i].members:
        lista.append(x.person_id)
counter=collections.Counter(lista)
print(counter)


#Reviso las edades por cada hogar
data=[]
for i in range(len(block_households)):
    print("CASA NUEVA",i+1," DE TIPO ", block_households[i].type," CON ID ",block_households[i].hh_id )
    for x in block_households[i].members:
        print("ID_Persona= ",x.person_id," Edad= ",x.age, "Sexo= ",x.sex)
        aux=[x.person_id,x.age,x.sex,block_households[i].hh_id]
        data.append(aux)
end = timeit.timeit()
print ("tiempo de ejecución= ",end - start)
frame_personas = pd.DataFrame(data, columns = ['Person ID', 'Age','Sex',"House ID"])
frame_personas.to_csv('personas.csv')


# In[28]:


for x in block_households:
    if x.hh_id==291:
        print(x.block_id)


# In[29]:


#Reviso las edades de la gente sobrante
if len(persons_in_block)==0:
    print("no sobraron personas")
else:    
    for x in persons_in_block:
        print("ID_Persona= ",x.person_id," Edad= ",x.age)






