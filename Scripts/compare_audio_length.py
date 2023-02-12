#############
##
## 描述：对比工程中英文资源长度并输出excel表
## Wwise选中对象: 单个中文资源所在的ActorMixer
## 支持对象命名格式: XXX_(M|F)_[CN|EN] 的SFX文件
## 输出：当前wwise项目的Scripts文件夹下名为中英文资源长度对照表.xlsx的excel表
## 注意事项：此脚本不支持Wwise自带的本地化处理方式，需给中英文各自创建SFX对象！！
## 使用案例：以中文语音的actormixer出发，输出NPC以及男女角色切换容器的各Sound对象中英文长度对比，切换容器默认男性长度，且对于资源字数进行预估和修改判定
##
#############


if __name__ != '__main__':
    print(f"error: {__file__} should not be imported, aborting script")
    exit(1)

import os
import sys
import pandas
import openpyxl

from waapi import WaapiClient, CannotConnectToWaapiException
from helpers import * # WAAPI相关接口函数

try:
    with WaapiClient() as client:

        selected_guid = get_selected_guid()
        resultDict = dict()
        resultDict["Sheet1"] = {"中文事件名": [], "英文事件名": [], "英文资源名": [], "中文_长度": [], "中文_字数预估" : [], "英文_长度": [], "长度差别": [], "是否需要修改": []}
        base_path = os.path.join(os.getcwd())
        project_path = os.path.dirname(object_get(client, from_ofType=["Project"], options=["filePath"])[0][0])
    
        print(project_path)
        # print(base_path)
        # print(selected_guid)
        r1 = dict()
        r2 = dict()
        r3 = dict()
        r4 = dict()
        tomatch_name = ""
        cur_mode = ["descendants"]
        if get_type_by_guid(client, selected_guid[0]) == "Sound":
            cur_mode = None

        # 默认检索Sound对象和切换容器
        for r0_id, r0_info in object_get(client, 
                          from_guid=selected_guid,
                          select_mode=cur_mode,
                          where_type_isIn=["Sound","SwitchContainer"],
                          options=["id", "name", "type"],
                          return_format="dict").items():
            tomatch_name = r0_info["name"].replace(" ", "_").replace("'", "_").replace("_M_", "_").replace("_F_", "_")

            if r0_info["type"] == "SwitchContainer":
                r1 = object_get(client, from_guid=[r0_id], select_mode=["descendants"], where_name_contains="Character", where_type_isIn=["AudioFileSource"], options=["id", "name","type", "audioSource:playbackDuration", "audioSource:trimValues"], return_format="dict")
            elif r0_info["type"] == "Sound":
                r1 = object_get(client, from_guid=[r0_id], select_mode=["children"], where_type_isIn=["AudioFileSource"], options=["id", "name","type", "audioSource:playbackDuration", "audioSource:trimValues"], return_format="dict")

            if len(r1) != 0:
                for _, r1_info in r1.items():
                    # 获取对应英文资源事件
                    en_event_name = (r0_info["name"][:-3]).replace(" ", "_").replace("'", "_").replace("_M_", "_").replace("_F_", "_") + "_EN"

                    r2 = object_get(client, from_path=["\\Events"],
                                      select_mode=["descendants"],
                                      where_name_matches="^" + en_event_name + "$",
                                      options=["id"])  
                    if len(r2) != 0 and r2[0] != None:
                        # 查询action
                        r3 = object_get(client, from_guid=[r2[0][0]], select_mode=["children"], options=["id", "name", "type", "@Target.id"], return_format="dict")   # 默认为第一个play的action
                        if len(r3) != 0:
                            for r3_id, r3_info in r3.items():

                                # 寻找source长度
                                if get_type_by_guid(client, r3_info["@Target.id"]) == "Sound":

                                    r4 = object_get(client, from_guid=[r3_info["@Target.id"]], where_type_isIn=["Sound"], options=["id", "name","audioSource:playbackDuration"], return_format="dict")

                                elif get_type_by_guid(client, r3_info["@Target.id"]) == "SwitchContainer": 

                                    r5 = object_get(client, from_guid=[r3_info["@Target.id"]], select_mode=["children"], where_name_contains="Character", where_type_isIn=["Sound"], options=["id", "name","audioSource:playbackDuration"], return_format="dict")
                                else:
                                    print("WARNING: could not find the corresponding length for: " + tomatch_name + " ,need additional check!")

                                if len(r4) != 0:
                                    for r4_id, r4_info in r4.items():
                                        cn_length = round(float(r1_info["audioSource:playbackDuration"]["playbackDurationMin"]), 2)
                                        en_length = round(float(r4_info["audioSource:playbackDuration"]["playbackDurationMin"]), 2)
                                        diff_length = en_length-cn_length

                                        if diff_length >= 0:
                                            need_change = "N"
                                        else:
                                            need_change = "Y"

                                        resultDict["Sheet1"]["中文事件名"].append(tomatch_name)
                                        resultDict["Sheet1"]["英文事件名"].append(en_event_name)
                                        resultDict["Sheet1"]["英文资源名"].append(r4_info["name"])
                                        resultDict["Sheet1"]["中文_长度"].append(cn_length)
                                        resultDict["Sheet1"]["中文_字数预估"].append(round(en_length*5,0))  # 预估中文字数需限制在英文长度乘以5内
                                        resultDict["Sheet1"]["英文_长度"].append(en_length)
                                        resultDict["Sheet1"]["长度差别"].append(diff_length)
                                        resultDict["Sheet1"]["是否需要修改"].append(need_change)

                                elif len(r4) == 0 and len(r5) != 0:
                                    for r5_id, r5_info in r5.items():
                                        cn_length = round(float(r1_info["audioSource:playbackDuration"]["playbackDurationMin"]), 2)
                                        en_length = round(float(r5_info["audioSource:playbackDuration"]["playbackDurationMin"]), 2)
                                        diff_length = en_length-cn_length

                                        if diff_length >= 0:
                                            need_change = "N"
                                        else:
                                            need_change = "Y"

                                        resultDict["Sheet1"]["中文事件名"].append(tomatch_name)
                                        resultDict["Sheet1"]["英文事件名"].append(en_event_name)
                                        resultDict["Sheet1"]["英文资源名"].append(r5_info["name"])
                                        resultDict["Sheet1"]["中文_长度"].append(cn_length)
                                        resultDict["Sheet1"]["中文_字数预估"].append(round(en_length*5,0))
                                        resultDict["Sheet1"]["英文_长度"].append(en_length)
                                        resultDict["Sheet1"]["长度差别"].append(diff_length)
                                        resultDict["Sheet1"]["是否需要修改"].append(need_change)
                                else:
                                    # 找不到对应的英文资源
                                    if ((tomatch_name.find("_M_") != -1) and (tomatch_name.find("_F_") != -1)):
                                        cn_length = round(float(r1_info["audioSource:playbackDuration"]["playbackDurationMin"]), 2)
                                        resultDict["Sheet1"]["中文事件名"].append(tomatch_name)
                                        resultDict["Sheet1"]["英文事件名"].append(en_event_name)
                                        resultDict["Sheet1"]["英文资源名"].append("")
                                        resultDict["Sheet1"]["中文_长度"].append(cn_length)
                                        resultDict["Sheet1"]["中文_字数预估"].append(0)
                                        resultDict["Sheet1"]["英文_长度"].append(0)
                                        resultDict["Sheet1"]["长度差别"].append(-cn_length)
                                        resultDict["Sheet1"]["是否需要修改"].append("Y")
                                        print("WARNING: could not find the EN event match for: " + tomatch_name)
                        else:
                            # 找不到对应的英文资源
                            if ((tomatch_name.find("_M_") != -1) and (tomatch_name.find("_F_") != -1)):
                                cn_length = round(float(r1_info["audioSource:playbackDuration"]["playbackDurationMin"]), 2)
                                resultDict["Sheet1"]["中文事件名"].append(tomatch_name)
                                resultDict["Sheet1"]["英文事件名"].append(en_event_name)
                                resultDict["Sheet1"]["英文资源名"].append("")
                                resultDict["Sheet1"]["中文_长度"].append(cn_length)
                                resultDict["Sheet1"]["中文_字数预估"].append(0)
                                resultDict["Sheet1"]["英文_长度"].append(0)
                                resultDict["Sheet1"]["长度差别"].append(-cn_length)
                                resultDict["Sheet1"]["是否需要修改"].append("Y")
                                print("WARNING: could not find the EN event match for: " + tomatch_name)
                    else:
                        # 找不到对应的英文事件
                        if ((tomatch_name.find("_M_") != -1) and (tomatch_name.find("_F_") != -1)):
                            cn_length = round(float(r1_info["audioSource:playbackDuration"]["playbackDurationMin"]), 2)
                            resultDict["Sheet1"]["中文事件名"].append(tomatch_name)
                            resultDict["Sheet1"]["英文事件名"].append("")
                            resultDict["Sheet1"]["英文资源名"].append("")
                            resultDict["Sheet1"]["中文_长度"].append(cn_length)
                            resultDict["Sheet1"]["中文_字数预估"].append(0)
                            resultDict["Sheet1"]["英文_长度"].append(0)
                            resultDict["Sheet1"]["长度差别"].append(-cn_length)
                            resultDict["Sheet1"]["是否需要修改"].append("Y")
                            print("WARNING: could not find the EN sound object match for: " + tomatch_name)
            else:
                if ((tomatch_name.find("_M_") != -1) and (tomatch_name.find("_F_") != -1)):
                    print("WARNING: could not find the length for: " + tomatch_name + " ,need additional check!")

    file_path = os.path.join(project_path, "Scripts\\中英文资源长度对照表.xlsx")

    with pandas.ExcelWriter(file_path) as writer:
        for info in resultDict:
            info_mark = pandas.DataFrame(resultDict[info])
            info_mark.to_excel(writer, engine='xlsxwriter', sheet_name=info, index=False)

except CannotConnectToWaapiException:
    print('Error', 'Could not establish the WAAPI connection. Is the Wwise Authoring Tool running?')
except RuntimeError as e:
    print('Error', f'{e}')
except Exception as e:
    import traceback

    print('Error', f'{e}\n\n{traceback.format_exc()}')
finally:
    print("Done")