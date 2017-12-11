
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def main(list_of_dicts, db, peewee_model, func, multi=False, upsert=True):
    """
      @Block
      :desc: This saves a list of dictionaries to a SQL table via
             the Peewee ORM as rows in the table, applying a user supplied
             func to each dictionary in the list, which must yield the desired
             row
  
      :param list_of_dicts: A list of dictionaries where each key corresponds
                            to an attribute of a Peewee model, which represents
                            a table with columns in SQL.
      :type list_of_dicts: list
      :example list_of_dicts: [{"gpi":"12405010000330", "name":"acyclovir",
                                "form":"Tablet", "dosage":"800 mg", "provider":"CVS",
                                "price":"19.27"}]
  
      :param peewee_model: A Peewee model, where the corresponding table has already
                           been created in the db.
      :type peewee_model: peewee.BaseModel
      :example peewee_model: class Drug(peewee.Model):
                                 date_pulled = peewee.DateTimeField()
                                 gpi = peewee.TextField()
                                 sc_id = peewee.TextField()
                                 site = peewee.TextField()
                                 name = peewee.TextField()
                                 form = peewee.TextField()
                                 dosage = peewee.TextField()
                                 quantity = peewee.TextField()
                                 provider = peewee.TextField()
                                 price = peewee.TextField()
  
                                 class Meta:
                                     database = db
  
  
      :param func: A user supplied function to be applied to each dictionary in the list_of_dicts,
      and yields the dictionary to be saved to the database
      :type func: a function
      :example func: def func(list_of_dicts):
                for x in list_of_dicts:
                  yield x 
  
      :param multi: A boolean indicating whether multiple processes will be connecting to the database
      :type multi: boolean
      :example multi: True 
  
      :param upsert: A boolean indicating to update on existing row
      :type upsert: boolean
      :example upsert: True 
    """
    if multi:
        db.get_conn()

    if len(list_of_dicts) > 4000:
        for group in chunker(list_of_dicts, 2000):
            with db.execution_context():
                peewee_model.insert_many(func(group)).upsert(upsert=upsert).execute()
    else:
        with db.execution_context():
            peewee_model.insert_many(func(list_of_dicts)).upsert(upsert=upsert).execute()






    if multi:
        db.close()
