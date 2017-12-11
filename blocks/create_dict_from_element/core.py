import logging
logger = logging.getLogger("whitecap_urls")
def main(element, settings, auxiliaries):
  """
  @Block
  :desc: apply settings functions to the element xpath creating a dictionary to save
  as the result 

  :param element: an html element from which you want to extract information 
  :type element: an html element 
  :example element: html.fromstring(resp.txt)

  :param settings: a list of dictionaries that specifies how to create the dictionary. Each 
  dictionary must contain the keys ["xpath", "keyName", "val", "func"], where "keyName" specifies
  the key to save the result of applying "func" to the xpath supplied in "xpath" to the element 
  "element". "func" must take a list, where the first element is the html-element  supplied
  as an input to create_dict_from_element and the second element of the list is the "xpath"
  key of the settings dictionary element 

  from the element 
  :type settings: list of dictionaries 
  :example settings:  [
        {"keyName": 'url',
         "xpath": ".//div[@class='image']/a",
         "func": get_url,
         "val": None}c
    ]

  :param auxiliaries: A list of dictionaries. The keys must contain ["keyName", "dependents", 
  "func", "val"]. If "dependents" is specified, "func" must take a list with the first element 
  being the dictionary created from applying the settings input, and the second element is the 
  "dependents" list. If dependents is none, aux_elem["val"] is set to the value of the return 
  dictionary
  previous elements 
  :type auxiliaries: list of dictionaries
  :example auxiliaries:   [
        {"keyName": 'run',
         "dependents": [],
         "func": None,
         "val": event['run']},
        {"keyName": 'site',
         "dependents": [],
         "func": None,
         "val": event['site']},
         {"keyName": 'page_num',
         "dependents": [],
         "func": None,
         "val": int(float(event['data']['beginIndex'])/ event['data']['pageSize']) + 1},
        {"keyName": 'site',
         "dependents": [],
         "func": None,
         "val": event['site']}

    ]

  :return: a dictionary with keys specfied by the keyName parameters in settings and auxiliaries 
  :rtype: dictionary
  """

  dict = {}
  for setting in settings:
      if setting['xpath']:
          try:
              dict[setting['keyName']] = setting['func']([element, setting['xpath']])
          except Exception as error:
              logger.warning("Failed in creating element {} {}".format(setting['keyName'], dict))
              dict[setting['keyName']] = None
              logger.warning(error)

      elif setting['val']:
          dict[setting['keyName']] = setting['val']
      else:
          logger.warning('Must have either xpath or value')

  if auxiliaries:
      for aux in auxiliaries:
          if aux['dependents']:
              try:
                  if type(aux['keyName']) is list:
                      vals = aux['func']([dict, aux['dependents']])
                      if type(vals) is list:
                          for key,val in zip(aux['keyName'], vals):
                              dict[key] = val
                      else:
                          if vals:
                              for key,val in vals.iteritems():
                                  dict[key] = val
                          else:
                              for key in aux['keyName']:
                                  dict[key] = None

                  else:
                    dict[aux['keyName']] = aux['func']([dict, aux['dependents']])
              except Exception as errornew:
                  logger.warning(errornew)
                  logger.warning("Failed in creating auxiliary element: {} {}".format(aux['keyName'],dict))
                  return {}

          else:
            dict[aux['keyName']] = aux['val']

  return dict
