import itertools
import pandas as pd

class Person:

    id_generator = itertools.count(1)

    def __init__(self, age, sex, role, education, activity):
        self.person_id = next(Person.id_generator)
        self.age = age
        self.sex = sex
        self.role = role
        self.education = education
        self.activity = activity

    def __str__(self): 
        if self.sex == 1:
            return "Person ID: {}\nMan, {} years old".format(self.person_id, self.age)
        else:
            return "Person ID: {}\nWoman {} years old".format(self.person_id, self.age)
    
    def as_tuple(self):
        return (self.person_id, self.age, self.sex, self.role, self.education)


class Household:
    # block_id=[]
    id_generator = itertools.count(1)

    def __init__(self, hh_type):
        self.members = []
        self.block_id=None
        self.hh_id = next(Household.id_generator)
        self.type = hh_type
        self.coord=[]

    def add_member(self, member):

        assert isinstance(member, Person), ('New member is not a Person instance.')
        self.members.append(member)

    def add_block_id(self, block_id):

        assert isinstance(block_id,int), ('New id is not a int')
        self.block_id=block_id 

     def add_coord(self, coord):
        self.coord=coord        
    

    def __str__(self):
        return 'Household ID: {}\n{} Members'.format(self.hh_id, len(self.members))
    
class Population:
    
    def __init__(self, individuals):
        
        self.individuals = individuals
            
    @classmethod
    def from_df(cls, df, cols):
        individuals = []
        for idx, row in df.iterrows():
            row = row[cols]
            individuals.append(Person(*row))
        return cls(individuals)
    
    def __str__(self):
        return "{} individuals population".format(len(self.individuals))
    
    def as_df(self):
        return pd.DataFrame([person.as_tuple() for person in self.individuals],
                             columns=['id', 'age', 'sex', 'role', 'education']).set_index('id')
        
        
        
    

        

if __name__ == '__main__':
    
    persons_data = pd.read_csv("data/personas_antofagasta.csv")

    persons = []

    for index, row in persons_data.iloc[:10].iterrows():

        persons.append(Person(row['P09'], row['P08'], row['P07'], row['P15'], row['P18']))
        print(persons[-1])

    