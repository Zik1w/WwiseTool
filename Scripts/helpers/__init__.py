import sys
import waapi as _w


def get_selected_guid():
    if len(sys.argv) == 2:
        return [sys.argv[1]]
    elif len(sys.argv) > 2:
        return sys.argv[1:]  # returns empty list on invalid range
    else:
        raise RuntimeError("ERROR: ", "Input cannot be recognized")


def get_selected_guids_list():
    return sys.argv[1:]  # returns empty list on invalid range


def object_get(client:_w.WaapiClient, 
                from_guid=None, from_search=None, from_name=None, from_path=None, from_ofType=None, from_query=None,
                select_mode=None, select_distinct=False,select_range=None,
                where_name_contains="", where_name_matches="", where_type_isIn=None,where_category_isIn=None,
                options=None,option_platform=None,option_language=None,
                filters=None,
                return_format="list"):

    obj_get_args = dict()
    args_transform=[]
    args_transform_where = []
    obj_get_opts=dict()
    cur_select_mode = None


    ## FROM Section

    if from_guid is not None:
        obj_get_args["from"] = {
                        "id": from_guid
                    }
    elif from_search is not None:
        obj_get_args["from"] = {
                        "search": from_search
                    }
    elif from_name is not None:
        obj_get_args["from"] = {
                        "name": from_name
                    }
    elif from_path is not None:
        obj_get_args["from"] = {
                        "path": from_path
                    }
    elif from_ofType is not None:
        obj_get_args["from"] = {
                        "ofType": from_ofType
                    }
    elif from_query is not None:
        obj_get_args["from"] = {
                        "query": from_query
                    }
    else:
        raise RuntimeError("ERROR: ", "FROM is not set")


    ## TRANSFORM Section

    obj_get_args["transform"] = []

    if select_mode is not None:
        cur_select_mode = select_mode
    elif from_search and from_name is not None:
        cur_select_mode = "children"
    elif from_path and from_ofType is not None:
        cur_select_mode = "descendants"
    else:
        cur_select_mode = None

    if cur_select_mode is not None:
        obj_get_args["transform"].append({"select": cur_select_mode})


    if select_distinct:
        obj_get_args["transform"].append("distinct")


    if select_range is not None:
        obj_get_args["transform"]["where"].append({"range": cur_select_mode})


    if where_name_contains is not None:
        obj_get_args["transform"].append({"where" : ["name:contains", where_name_contains]})

    if where_name_matches is not None:
        obj_get_args["transform"].append({"where" : ["name:matches", where_name_matches]})

    if where_type_isIn is not None:
        obj_get_args["transform"].append({"where" : ["type:isIn", where_type_isIn]})

    if where_category_isIn is not None:
        obj_get_args["transform"].append({"where" : ["category:isIn", where_category_isIn]})


    if not obj_get_args["transform"]:
        print("WARNING: ", "TRANSFORM is not set")


    ## OPTION Section
    if options is not None:
        obj_get_opts["return"] = options

    if option_platform is not None:
        obj_get_opts["platform"] = option_platform

    if option_language is not None:
        obj_get_opts["language"] = option_language
        
    results = client.call("ak.wwise.core.object.get", obj_get_args, options=obj_get_opts)


    ## RETURN Section
    retval = []
    if results != None:
        results_list = results["return"]

        if return_format == "list":
            for i in range(len(results_list)):
                retval.append(tuple(results_list[i].values()))  ##DOESN'T GURANTEE ORDER!!
        elif return_format == "dict":
            retval = dict()

            for i in range(len(results_list)):
                retval[results_list[i]["id"]] = results_list[i]
        else:
            raise RuntimeError("ERROR: ", "The return format is not recognized")

    else:
        print("WARNING: ", "No such value found")
        if return_format == "list":
            return []
        elif return_format == "dict":
            return dict()
        else:
            raise RuntimeError("ERROR: ", "The return format is not recognized")

    ##Custom FILTER Section
    retval_filtered = []

    if filters is None:
        return retval
    else:
        retval_filtered = []

        for i in range(len(retval)):

            property_value = 0
            for j in range(len(filters)):
                p_name = filters[j].split(".")[1].split(":")[0]
                p_value = filters[j].split(".")[1].split(":")[1]

                if p_value.isdigit():
                    property_value = float(p_value)
                elif p_value.replace('.','',1).isdigit():
                    property_value = float(p_value)
                elif p_value == "true":
                    property_value = True
                elif p_value == "false":
                    property_value = False
                else:
                    print("WARNING: ", "the custom filter value can not be recognized, return original results")
                    return retval

            if get_property_value(client, retval[i][0], p_name, 1) == property_value:
                retval_filtered.append(retval[i])

        return retval_filtered




### CREATE FUNC

def object_create(client:_w.WaapiClient, parent_obj, obj_type, obj_name,
                    onNameConflict="fail", platform=None, autoAddToSourceControl=None,
                    notes=None, children=None):

    obj_create_args = dict()
    args_transform=[]
    args_transform_where = []
    obj_get_opts=dict()
    cur_select_mode = None

    if parent_obj is not None:
        obj_create_args["parent"] = parent_obj
    else:
        raise RuntimeError("invalid input, need parent for new object")


    if obj_type is not None:
        obj_create_args["type"] = obj_type
    else:
        raise RuntimeError("invalid input, need type for new object")


    if obj_name is not None:
        obj_create_args["name"] = obj_name
    else:
        raise RuntimeError("invalid input, need name for new object")


    obj_create_args["onNameConflict"] = onNameConflict


    retval = client.call("ak.wwise.core.object.create", obj_create_args)
    

    if retval is not None:
        if retval["id"] is not None:
            return retval["id"] 
        else:
            print("WARNING: ", "no object created")
    else:
        print("WARNING: ", "no object created")

    return None 



### GET FUNC

def get_path_by_guid(client:_w.WaapiClient, obj_guid):

    obj_get_args = {
        "from": {
            "id": [obj_guid]
        }
    }


    opts_query = {
        "return": ["path"]
    }

    retval = client.call("ak.wwise.core.object.get", obj_get_args, options=opts_query)

    if retval is not None:
        if retval["return"] is not None:
            if retval["return"][0]["path"] is not None:
                return retval["return"][0]["path"] 
            else:
                print("WARNING: ", "no object with id: " + obj_guid)
        else:
            print("WARNING: ", "no object with id: " + obj_guid)
    else:
        print("WARNING: ", "no object with id: " + obj_guid)
            
    return None


def get_name_by_guid(client:_w.WaapiClient, obj_guid):

    obj_get_args = {
        "from": {
            "id": [obj_guid]
        }
    }


    opts_query = {
        "return": ["name"]
    }

    retval = client.call("ak.wwise.core.object.get", obj_get_args, options=opts_query)

    if retval is not None:
        if retval["return"] is not None:
            if retval["return"][0]["name"] is not None:
                return retval["return"][0]["name"] 
            else:
                print("WARNING: ", "no object with id: " + obj_guid)
        else:
            print("WARNING: ", "no object with id: " + obj_guid)
    else:
        print("WARNING: ", "no object with id: " + obj_guid)
            
    return None


def get_guid_by_name(client:_w.WaapiClient, obj_name):

    obj_get_args = {
        "from": {
            "name": [obj_name]
        }
    }


    opts_query = {
        "return": ["id"]
    }

    retval = client.call("ak.wwise.core.object.get", obj_get_args, options=opts_query)

    if retval is not None:
        if retval["return"] is not None:
            if retval["return"][0]["id"] is not None:
                return retval["return"][0]["id"] 
            else:
                print("WARNING: ", "no object with id: " + obj_name)
        else:
            print("WARNING: ", "no object with id: " + obj_name)
    else:
        print("WARNING: ", "no object with id: " + obj_name)
            
    return None


def get_type_by_guid(client:_w.WaapiClient, obj_guid):

    obj_get_args = {
        "from": {
            "id": [obj_guid]
        }
    }


    opts_query = {
        "return": ["type"]
    }

    retval = client.call("ak.wwise.core.object.get", obj_get_args, options=opts_query)

    if retval is not None:
        if retval["return"] is not None:
            if retval["return"][0]["type"] is not None:
                return retval["return"][0]["type"] 
            else:
                print("WARNING: ", "no object with id: " + obj_guid)
        else:
            print("WARNING: ", "no object with id: " + obj_guid)
    else:
        print("WARNING: ", "no object with id: " + obj_guid)
            
    return None


def get_parent_guid(client:_w.WaapiClient, obj_guid):
    obj_get_args = {
        "from": {
            "id": [obj_guid]
        },
        "transform": [
            {"select": ["parent"]}
        ]
    }


    opts_query = {
        "return": ["id"]
    }

    retval = client.call("ak.wwise.core.object.get", obj_get_args, options=opts_query)

    if retval is not None:
        if retval["return"] is not None:
            if retval["return"][0]["id"] is not None:
                return retval["return"][0]["id"] 
            else:
                print("WARNING: ", "no object with id: " + obj_guid)
        else:
            print("WARNING: ", "no object with id: " + obj_guid)
    else:
        print("WARNING: ", "no object with id: " + obj_guid)
            
    return None


def get_property_value(client:_w.WaapiClient, obj_guid, prop_name):


    obj_get_args = {
        "from": {
            "id": [obj_guid]
        }
    }


    opts_query = {
        "return": ["id", "name", "type", prop_name] ##return include id, name, type by default
    }

    retval = client.call("ak.wwise.core.object.get", obj_get_args, options=opts_query)

    if retval != None:
        return retval["return"][0]

    else:
        print ("WARNING: ", "value cannot be found")
        return None



### SET FUNC

def set_property_value(client:_w.WaapiClient, obj_guid, prop_name, newval):

    object_set_args = {
        "object": obj_guid,
        "property": prop_name,
        "value": newval
    }

    retval = client.call("ak.wwise.core.object.setProperty", object_set_args)
    
    return retval


def set_reference(client:_w.WaapiClient, obj, ref, value, platform=None):

    obj_setReference_args=dict()

    obj_setReference_args["object"] = obj
    obj_setReference_args["reference"] = ref
    obj_setReference_args["value"] = value

    retval = client.call("ak.wwise.core.object.setReference", obj_setReference_args)

    return retval



## MOVE FUNC

def move_object(client:_w.WaapiClient, obj, parent, onNameConflict="fail"):

    obj_move_args=dict()

    obj_move_args["object"] = obj
    obj_move_args["parent"] = parent


    retval = client.call("ak.wwise.core.object.move", obj_move_args)
    
    if retval is not None:
        if retval["id"] is not None:
            return retval["id"] 
        else:
            print("WARNING:no object with id: " + obj)
    else:
        print("WARNING:no object with id: " + obj)

    return None



## UNDO FUNC

def begin_undo_group(client:_w.WaapiClient):

    obj_undo_args=dict()

    retval = client.call("ak.wwise.core.undo.beginGroup", obj_undo_args)

    return retval


def perform_undo(client:_w.WaapiClient):

    obj_undo_args=dict()

    retval = client.call("ak.wwise.core.undo.undo", obj_undo_args)

    return retval


def end_undo_group(client:_w.WaapiClient, display_name):

    obj_undo_args={
        "displayName" : display_name
    }

    retval = client.call("ak.wwise.core.undo.endGroup", obj_undo_args)

    return retval

