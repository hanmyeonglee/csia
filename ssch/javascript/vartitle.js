import { form, copy, errorHandling, loading } from "./formCover.js";
const dises =
  "호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(
    " "
  );
const diags =
  "보건실휴식 타세놀 모드코 모드콜 모드코프 쎄로테정 지르텍 리놀 화이투벤큐노즈 화이투벤큐 부스코판플러스 부루펜 아나프록스정 탁센 그날엔 이지엔식스이브 이지엔식스 탁센레이디 정로환 베아제 훼스탈 마로이신 나조린 아이투오 케프란 신폴에이 스타빅 알마겔 포타겔 coban 후시메드 밴드 에어파스 멸균안대 생리대 자가키트 거즈 탄력붕대 바세린 오라메디 페리덱스 알보칠 아프니벤큐 쎄레스톤지 제올라 버물리 아즈렌 하이맘번 드레싱밴드 생리식염수 애니클린 리도맥스 타세놀콜드 호올스 포도당캔디 애드빌 비코그린 베나치오 맥시롱 쌍화탕 콜대원 백초 써버쿨 타이레놀우먼 반창고 타벡스겔 아이스팩 핫팩".split(
    " "
  );

/**
 * pursue
 * 0 = connect request
 * 1 = information request
 * 2 = add wait patient request
 * 3 = delete patient from waiter list request
 * 4 = bed number inc/dec request
 * 5 = diagnosis (im)possible request
 * 6 = not request, just response, confirm by server
 * 7 = add patient to daily db
 * 8 = edit daily db
 * 9 = delete patient from daily db
 */

const webIO = new WebSocket("ws://192.168.1.117:52125");
const locate = location.href.split("/ssch/")[1];
const table = document.querySelector("#tableCover");
const row = document.querySelector(".tableElements");
const waiterList = document.getElementById("waiterList");
const waiterForm = document.getElementById("infoCoverExample");
const body = document.querySelector("body");
const confirmModal = document.getElementById("confirmOBtn");
const diagBtn = document.getElementById("diagPos");
const bedBtn = document.getElementById("bedNum");
const diseList = document.getElementById("diseaseList");
const diagList = document.getElementById("diagList");
const listItem = document.getElementById("listGroupItemExample");
const applyButton = document.querySelector(".applyTable");
const changeList = ["id", "number", "name", "sex", "disease", "treat", "time"];
const diseaseCover = document.getElementById("diseaseDropdownCover");
const treatmentCover = document.getElementById("treatmentDropdownCover");
const download = document.querySelector(".downloadBtn");
let waiters = [];
let daily = [];
let diagPos = false;
let bedNum = 4;
let tempConfirm = undefined;
let dailyList = [];
let remake = false;
document.querySelector("#tableCover").removeChild(row);
body.removeChild(waiterForm);
body.removeChild(listItem);
listItem.id = "";

const makeDiseaseList = (parent, suffix) => {
  for (let i = 0; i < dises.length; i++) {
    let d = dises[i];
    let tempItem = listItem.cloneNode(true);
    tempItem.querySelector("input").value = d;
    tempItem.querySelector("input").id = `sym${String(i).padStart(
      2,
      "0"
    )}${suffix}`;
    tempItem.querySelector("label").innerText = d;
    tempItem
      .querySelector("label")
      .setAttribute("for", `sym${String(i).padStart(2, "0")}${suffix}`);
    tempItem.removeAttribute("hidden");
    parent.appendChild(tempItem);
  }
};

const makeTreatList = (flag = false, parent, suffix) => {
  for (let i = 0; i < diags.length; i++) {
    let d = diags[i];
    let tempItem = listItem.cloneNode(true);
    tempItem.querySelector("input").value = d;
    tempItem.querySelector("input").id = `treat${String(i).padStart(
      2,
      "0"
    )}${suffix}`;
    tempItem.querySelector("label").innerText = d;
    tempItem.querySelector("input").classList.remove("disease");
    tempItem.querySelector("input").classList.add("treat");
    tempItem
      .querySelector("label")
      .setAttribute("for", `treat${String(i).padStart(2, "0")}${suffix}`);
    tempItem.removeAttribute("hidden");
    if (d == "보건실휴식" && flag) {
      tempItem.querySelector("input").classList.add("bed");
    }
    parent.appendChild(tempItem);
  }
};

makeDiseaseList(diseList, 0);
makeTreatList(true, diagList, 0);

/**
 *
 * @param {object} data : id, number, name, sex, time, symptom, diag object
 */
const makeTable = (data) => {
  let tempRow = row.cloneNode(true);
  let valVerify = {};
  for (let query of changeList) {
    let tmp = tempRow.querySelector(`.${query}Data`);
    tmp.value = data[query];
    valVerify[query] = tmp;
    if (query == "disease" || query == "treat") {
      let drdw = tmp.parentElement.querySelector(".dropdown-menu");
      query == "disease"
        ? makeDiseaseList(drdw, data["id"])
        : makeTreatList(false, drdw, data["id"]);
      drdw.addEventListener("click", (e) => {
        let inp = drdw.querySelectorAll(`.form-check-input.${query}`);
        let text = drdw.parentElement.querySelector("input[type='text']");
        let write = [];
        for (let i of inp) {
          if (i.checked) {
            write.push(i.value);
          }
        }
        text.value = write.join(", ");
      });
    }
  }
  let delBtn = tempRow.querySelector("svg.delBtn");
  delBtn.addEventListener("click", async (e) => {
    let flag = confirm("정말로 삭제하시겠습니까? 영구적으로 삭제됩니다.");
    if (flag) {
      let fetchInfo = data['uniq'];
      await webIO.send(
        form({ type: 9, stat: 1, header: "t", body: fetchInfo })
      );
    } else {
      return;
    }
  });
  table.appendChild(tempRow);
  dailyList.push([copy(data), valVerify]);
};

const makeTableAll = () => {
  let exVal = table.querySelectorAll(".oneRow.tableElements");
  for (let val of exVal) {
    table.removeChild(val);
  }
  for (let data of daily) {
    makeTable(data);
  }
};

const deleteWaiter = (crit) => {
  waiters = waiters.filter((waiter) => {
    return waiter["uniq"] != crit;
  });
  makeListAll();
};

const pprint = (timeExp) => {
  let t = timeExp.split(":");
  return `${t[0].padStart(2, "0")}:${t[1].padStart(2, "0")}`;
};

/**
 *
 * @param {object} data : id, number, name, sex, time, symptom object
 */
const makeList = (data, num) => {
  let tempWaiter = waiterForm.cloneNode(true);
  tempWaiter.removeAttribute("hidden");
  tempWaiter.id = data["uniq"];
  tempWaiter.querySelector(".numInfo").innerText = num;

  let content = tempWaiter.querySelector(".nameInfo");
  content.innerText = `${data["name"]}, ${pprint(data["time"])}`;
  tempWaiter.classList.add(`${data["uniq"]}`);

  tempWaiter.querySelector(".dropdownQuote").innerHTML = `${data["number"]} ${
    data["name"]
  }(${data["sex"]})에 대한 상세정보<br><br>예약된 시간: ${pprint(
    data["time"]
  )}<br>증상: ${data["symptom"]}`;

  let btnO = tempWaiter.querySelector(".confirmO");
  btnO.addEventListener("click", (e) => {
    tempConfirm = copy(data);
    confirmModal.querySelector(
      "#confirmModalTitle"
    ).innerText = `${data["name"]}의 처치 기록`;
    confirmModal.querySelector("#confirmModalSymptom").value = data["symptom"];
    confirmModal.querySelector("#hiddenInfo").value = data["uniq"];
  });

  let btnX = tempWaiter.querySelector(".confirmX");
  btnX.addEventListener("click", async (e) => {
    let flag = confirm("정말로 삭제하시겠습니까?");
    if (flag) {
      await webIO.send(
        form({ type: 3, stat: 1, header: "t", body: {"uniq":data["uniq"], "time":data["time"]} })
      );
      deleteWaiter(data["uniq"]);
    } else {
      return;
    }
  });

  waiterList.appendChild(tempWaiter);
};

const makeListAll = () => {
  waiterList.innerHTML = "";
  for (let i = 0; i < waiters.length; i++) {
    makeList(waiters[i], i + 1);
  }
};

const downloadFile = async (filename) => {
  const response = await fetch(`./csv/${filename}.xlsx`);
  const file = await response.blob();
  const downloadUrl = window.URL.createObjectURL(file); // 해당 file을 가리키는 url 생성

  const anchorElement = document.createElement("a");
  anchorElement.setAttribute("hidden", true);
  document.body.appendChild(anchorElement);
  anchorElement.download = `${filename}.xlsx`;
  anchorElement.href = downloadUrl; // href에 url 달아주기

  anchorElement.click(); // 코드 상으로 클릭을 해줘서 다운로드를 트리거

  document.body.removeChild(anchorElement); // cleanup - 쓰임을 다한 a 태그 삭제
  window.URL.revokeObjectURL(downloadUrl); // cleanup - 쓰임을 다한 url 객체 삭제
};

webIO.onopen = async () => {
  console.log("WebSocket Opened");
  await webIO.send(form({ type: 0, header: "t" }));
};

webIO.onclose = () => {
  console.log("WebSocket Closed");
};

webIO.onmessage = async (data) => {
  let message = JSON.parse(data.data);
  console.log(message);
  let stat = message["stat"];
  let head = message["content"]["header"];
  let returnType = message["content"]["body"]["return"];
  let innerData = message["content"]["body"]["body"];
  if (stat != 1) {
    errorHandling({ reload: true, locate: locate });
  } else {
    if (head == 6) {
      switch (returnType) {
        case 0:
          await webIO.send(form({ type: 1, header: "t" }));
          break;
        case 1:
          /*
                        waiterInfo의 구조
                        {
                            waiters : [{id:1, number:~, name:~, symptom:~, sex:~}, ... ],
                            daily : [{id:1, number:~, name:~, symptom:~, diag:~, sex:~, time:~}, ... ]
                            diagPos : T/F,
                            bedNum : 0~4
                        }
                    */
          let waiterInfo = copy(innerData);
          console.log(waiterInfo);
          waiters = waiterInfo["waiters"];
          daily = waiterInfo["daily"];
          diagPos = waiterInfo["diagPos"];
          bedNum = waiterInfo["bedNum"];
          makeTableAll();
          makeListAll();
          diagBtn.src = diagPos
            ? "./image.resize/diagPos.reduct.png"
            : "./image.resize/diagImpos.reduct.png";
          bedBtn.src = `./image.resize/bedRemain0${bedNum}.reduct.png`;
          break;
        case 3:
        case 4:
        case 5:
          loading(true);
          break;
        case 7:
        case 9:
          daily = copy(innerData);
          makeTableAll();
          loading(true);
          break;
        case 8:
          if(remake){
            daily.sort((a, b) => {return a['time'].localeCompare(b['time']);})
            makeTableAll();
          }
          loading(true);
          alert("등록되었습니다.");
          break;
        case 10:
          downloadFile(innerData);
          break;
        default:
          errorHandling({ reload: true, locate: locate });
          break;
      }
    } else if (head == 2) {
      waiters.push(copy(innerData));
      makeListAll();
    } else {
      errorHandling({ reload: true, locate: locate });
    }
  }
};

confirmModal
  .querySelector("#confirmModalBtn")
  .addEventListener("click", async (e) => {
    loading();
    let diseInp = confirmModal.querySelectorAll(".form-check-input.disease");
    let treatInp = confirmModal.querySelectorAll(".form-check-input.treat");
    let bedFlag = treatmentCover.querySelector(".bed").checked;
    let diseVal =
      diseaseCover.parentElement.querySelector("input[type='text']");
    let treatVal =
      treatmentCover.parentElement.querySelector("input[type='text']");
    if (diseVal.value.trim().length == 0) {
      errorHandling({ message: "병명을 입력해주십시오." });
      loading(true);
      return;
    }
    if (treatVal.value.trim().length == "0") {
      errorHandling({ message: "처치를 입력해주십시오." });
      loading(true);
      return;
    }
    let contents = copy(tempConfirm);
    contents["disease"] = diseVal.value.trim();
    contents["treat"] = `${contents["symptom"]} : ${treatVal.value.trim()}`;
    delete contents.symptom;

    let information = confirmModal.querySelector("#hiddenInfo").value;
    if (bedFlag) {
      if (bedNum == 0) {
        errorHandling({ message: "이미 침대가 꽉 찼습니다." });
        loading(true);
        return;
      }
      bedNum--;
      await webIO.send(form({ type: 4, stat: 1, header: "t", body: -1 }));
      bedBtn.src = `./image.resize/bedRemain0${bedNum}.reduct.png`;
    }

    // content: id, number, name, sex, time, disease, treat object
    await webIO.send(form({ type: 7, stat: 1, header: "t", body: contents }));
    deleteWaiter(information);

    for (let tmp of diseInp) {
      tmp.checked = false;
    }
    for (let tmp of treatInp) {
      tmp.checked = false;
    }
    diseVal.value = "";
    treatVal.value = "";
  });

diagBtn.addEventListener("click", async (e) => {
  diagPos = !diagPos;
  diagBtn.src = diagPos
    ? "./image.resize/diagPos.reduct.png"
    : "./image.resize/diagImpos.reduct.png";
  await webIO.send(form({ type: 5, stat: 1, header: "t", body: diagPos }));
});

bedBtn.addEventListener("click", async () => {
  let flag = confirm("사용 가능 침대수를 하나 늘리시겠습니까?");
  if (flag) {
    if (bedNum == 4) {
      errorHandling({ message: "이미 모두 비어있습니다." });
      return;
    }
    bedNum++;
    await webIO.send(form({ type: 4, stat: 1, header: "t", body: 1 }));
    bedBtn.src = `./image.resize/bedRemain0${bedNum}.reduct.png`;
  }
});

applyButton.addEventListener("click", async (e) => {
  let ret = {};
  let flag = false;
  for (let subList of dailyList) {
    let origin = subList[0];
    let change = subList[1];
    let crit = origin["uniq"];
    for (let query of changeList) {
      if (origin[query] != change[query].value) {
        flag = true;
        if (!(crit in ret)) {
          ret[crit] = [[query, change[query].value]];
        } else {
          ret[crit].push([query, change[query].value]);
        }
        origin[query] = change[query].value;
        if (query == "disease" || query == "treat") {
          for (let inp of change[
            query
          ].parentElement.parentElement.querySelectorAll(
            `.form-check-input.${query}`
          )) {
            inp.checked = false;
          }
        } else if (query == "time"){
          remake = true;
          for(let day of daily){
            if(day['uniq'] == crit){
              day['time'] = origin[query];
              break;
            }
          }
        }
      }
    }
  }
  if (flag) {
    await webIO.send(form({ type: 8, stat: 1, header: "t", body: ret }));
  } else {
    return;
  }
});

diseaseCover.querySelector(".dropdown-menu").addEventListener("click", (e) => {
  let diseInp = diseaseCover.querySelectorAll(".form-check-input.disease");
  let diseText = diseaseCover.parentElement.querySelector("input[type='text']");
  let write = [];
  for (let dise of diseInp) {
    if (dise.checked) {
      write.push(dise.value);
    }
  }
  diseText.value = write.join(", ");
});

treatmentCover
  .querySelector(".dropdown-menu")
  .addEventListener("click", (e) => {
    let treatInp = treatmentCover.querySelectorAll(".form-check-input.treat");
    let treatText =
      treatmentCover.parentElement.querySelector("input[type='text']");
    let write = [];
    for (let treat of treatInp) {
      if (treat.checked) {
        write.push(treat.value);
      }
    }
    treatText.value = write.join(", ");
  });

download.addEventListener("click", async (e) => {
  if (
    confirm("이 시점까지의 기록들이 다운로드됩니다. 다운로드 하시겠습니까?")
  ) {
    await webIO.send(form({ type: 10, stat: 1, header: "t" }));
  }
});
