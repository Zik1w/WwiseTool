#############
##
## 描述：将指定命名的Sound对象按特定切换变量进行批量自动配置
## Wwise选中对象: 多个角色类的ActorMixer
## 支持对象命名格式: 自定义的文件检索名
## 输出：当前wwise项目的Scripts文件夹下名为中英文资源长度对照表.xlsx的excel表
## 注意事项：此脚本不支持Wwise自带的本地化处理方式，需给中英文各自创建SFX对象！！
## 使用案例：此脚本以_M/F_区分男女角色自动生成并配置切换容器参数（Male/Female)
##
#############


if __name__ != "__main__":
    print(f"error: {__file__} should not be imported, aborting script")
    exit(1)


import os
import sys

from waapi import WaapiClient, CannotConnectToWaapiException
from helpers import * # WAAPI相关接口函数


CHARACTER_TYPE_SWITCH_GROUP_NAME = "Character"   ## 切换变量名称
CHARACTER_TYPE_SWITCH_DEFAULT_NAME = "Male"      ## 切换变量参数
CHARACTER_TYPE_SFX_NAME_REGEX = "^" + "[a-zA-Z0-9:_ ]+_M_[a-zA-Z0-9:_ ]+" + "[CN|EN]" + "$" ##需创建切换容器的Sound对象名称正则检索

def get_switches_for_group_type(client:WaapiClient):
    sw_name_to_guid = dict()
    for sg_guid, sg_name in object_get(client, from_search=[CHARACTER_TYPE_SWITCH_GROUP_NAME], where_type_isIn=["SwitchGroup"], options=["id", "name"]):
        if sg_name == CHARACTER_TYPE_SWITCH_GROUP_NAME:
            for sw_guid, sw_name in object_get(
                    client, from_guid=[sg_guid], select_mode=["children"], where_type_isIn=["Switch"], options=["id", "name"]):
                sw_name_to_guid[sw_name] = sw_guid
            break
    return sw_name_to_guid

try:
    selected_guids = get_selected_guid()
    base_path = os.path.join(os.getcwd())

    print(base_path)
    print(selected_guids)

    if len(selected_guids) == 0:
        print("Info", "No objects were selected")
        exit(0)

    with WaapiClient() as client:
        project_path = object_get(client, from_ofType=["Project"], options=["filePath"])

        obj_names = [get_name_by_guid(client, guid) for guid in selected_guids]
        if None in obj_names:
            raise RuntimeError("Could not get names of all selected objects")

        switches = get_switches_for_group_type(client)
        if len(switches) == 0:
            raise RuntimeError(f"Could not find switches for group {CHARACTER_TYPE_SWITCH_GROUP_NAME}")
        
        begin_undo_group(client)

        for m_id, m_name in object_get(client, from_guid=selected_guids, select_mode=["descendants"], 
                                    where_name_matches=CHARACTER_TYPE_SFX_NAME_REGEX,  
                                    where_type_isIn=["Sound"], 
                                    options=["id", "name"]): 

            parent_obj = get_parent_guid(client, m_id)
            if parent_obj is None:
                raise RuntimeError(f"{m_id} has no parent")

            if get_type_by_guid(client, parent_obj) == "SwitchContainer":
                print(f"{m_name} is already in a switchContainer, no need to act")
                continue

            sc_name = m_name.replace("_M_", "_")   ##switch container

            sc_obj = object_create(client, parent_obj, "SwitchContainer", sc_name, onNameConflict="replace")
            if sc_obj is not None:
                set_reference(client, sc_obj, "SwitchGroupOrStateGroup", f"SwitchGroup:{CHARACTER_TYPE_SWITCH_GROUP_NAME}")
                set_reference(client, sc_obj, "DefaultSwitchOrState", switches[CHARACTER_TYPE_SWITCH_DEFAULT_NAME])
            else:
                # 中途失败回退
                end_undo_group(client, "refactor into character body type")
                perform_undo(client)
                raise RuntimeError("Could not create switch container under " +
                                   str(get_name_by_guid(client, parent_obj)))

            # 重新reparent
            res = move_object(client, m_id, sc_obj)
            if sc_obj is None:
                # 中途失败回退
                end_undo_group(client, "refactor into character body type")
                perform_undo(client)
                raise RuntimeError("Could not create switch container under " +
                                   str(get_name_by_guid(client, parent_obj)))

            f_name = m_name.replace("_M_", "_F_")

            female_info = object_get(client, from_guid=[parent_obj], select_mode=["descendants"], where_name_contains=f_name, where_type_isIn=["Sound"], options=["id", "name"])

            for f_id, f_name in female_info:
                res_move = move_object(client, f_id, sc_obj)
                if res_move is None:
                    # 中途失败回退
                    end_undo_group(client, "refactor into character body type")
                    perform_undo(client)
                    raise RuntimeError("Could not move object: "+ f_id)

            obj_assignments = []
            obj_sounds = []
            obj_sounds.append((m_id, m_name))

            for x in female_info:
                obj_sounds.append(x)

            # 此处以男(Male)和女(Female)两者为例对切换容器进行配置
            for obj_guid, obj_name in obj_sounds:
                if obj_name.find("_M") != -1 and obj_name.lower().find("character") != -1:
                    obj_assignments.append((obj_guid, switches["Male"]))
                elif obj_name.find("_F") != -1 and obj_name.lower().find("character") != -1:
                    obj_assignments.append((obj_guid, switches["Female"]))

            for obj_guid, sw_guid in obj_assignments:
                res_assign = client.call("ak.wwise.core.switchContainer.addAssignment",
                            {"child": obj_guid, "stateOrSwitch": sw_guid})

            create_event_args = {
                "parent": "\\Events\\Default Work Unit",
                "type": "Event",
                "name": sc_name,
                "onNameConflict": "fail",
                "children": [
                    {
                        "name": "",
                        "type": "Action",
                        "@ActionType": 1,
                        "@Target": get_path_by_guid(client, sc_obj)

                    }
                ]
            }

            res = client.call("ak.wwise.core.object.create", create_event_args)

            # 中途失败回退
            if res is None:
                end_undo_group(client, "refactor into character body type")
                perform_undo(client)

        end_undo_group(client, "refactor into character body type")


except CannotConnectToWaapiException:
    print("Error: ", "Could not establish the WAAPI connection. Is the Wwise Authoring Tool running?")
except RuntimeError as e:
    print("Error: ", f"{e}")
except Exception as e:
    import traceback

    print("Error: ", f"{e}\n\n{traceback.format_exc()}")
finally:
    print("Done!")
