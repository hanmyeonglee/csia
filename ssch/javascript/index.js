import { WsClient, copy, errorHandling, loading } from "./formCover.js";
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
const examineCurrentInterface = (inters) => {
  return getComputedStyle(inters[0]).display == "none" ? inters[1] : inters[0];
};
(() => {
  let temp = new Date();
  let yy = temp.getFullYear().toString().substring(2, 4);
  let mm = (temp.getMonth() + 1).toString().padStart(2, "0");
  let dd = temp.getDate().toString().padStart(2, "0");
  let DD = temp.toString().substring(0, 3);

  Array.from(document.getElementsByClassName("dayTime")).forEach((element) => {
    element.innerText = `${yy}.${mm}.${dd} (${DD})`;
  });
})();

const webIO = new WsClient(new WebSocket("ws://localhost:52125"));
const interfaces = document.getElementsByClassName("interface");
const applyBtns = Array.from(document.getElementsByClassName("applyBtn"));
const modal = document.getElementById("symptomType");
const hourSelect = Array.from(document.getElementsByClassName("hour"));
const diagPosImg = Array.from(document.getElementsByClassName("diagPos"));
const bedNumImg = Array.from(document.getElementsByClassName("bedNum"));
const about = document.getElementById("about");
const logo = document.querySelector(".imgResize.center.navImg01");
const names = ["chrome", "edge", "safari", "windows", "mac", "android", "ios"]
let diagPos = false;
let bedNum = 4;
let current = examineCurrentInterface(interfaces);
let symptom = [];
let appointedTime = {};
let other = false;
let key = null;
let iv = null;
let pubkey = null;

const verify = (data) => {
  let ret = {};

  let number = data["number"];
  let number_info = number[number.options.selectedIndex].value;
  if (number_info == "default") {
    throw Error("학년/반");
  } else {
    ret["number"] = number_info;
  }

  let name_info = data["name"].value;
  if (name_info) {
    ret["name"] = name_info;
  } else {
    throw Error("이름");
  }

  let checked;
  for (let g of data["sex"]) {
    if (g.checked) {
      checked = g;
    }
  }
  ret["sex"] = checked.value == "m" ? "남" : "여";

  if (symptom.length == 0 && !other) {
    throw Error("증상");
  } else {
    if (other) {
      let val = data["otherSymptom"].value.trim();
      if (val != "") {
        symptom.push(val);
      } else {
        throw Error("그 외 증상");
      }
    }
  }
  ret["symptom"] = symptom.join(", ");

  let hour = data["time"][0];
  let minute = data["time"][1];
  let hour_info = hour[hour.options.selectedIndex].value;
  let minute_info = minute[minute.options.selectedIndex].value;
  if (hour_info == "default") {
    throw Error("시간 : 시");
  } else if (minute_info == "default") {
    throw Error("시간 : 분");
  } else {
    ret["time"] = `${hour_info}:${minute_info}`;
  }

  return ret;
};

const makeOptions = () => {
  let hour = new Date().getHours();
  let hourDefaultOption =
  '<option value="default" class="default" selected>시(hour)</option>';
  let minuteDefaultOption =
  '<option value="default" class="default" selected>분(minute)</option>';
  let optionForm = (num, mes, disable) => {
    let ret = document.createElement("option");
    ret.value = String(num).padStart(2, "0");
    ret.innerText = `${num}${mes}`;
    if (disable) {
      ret.setAttribute("disabled", true);
      ret.style.color = "red";
    } else {
      ret.style.color = "green";
    }
    return ret;
  };
  
  hourSelect.forEach((element) => {
    element.innerHTML = hourDefaultOption;
    for (let i = 8; i <= 16; i++) {
      //element.appendChild(optionForm(i, "시", (i >= hour) ? false : true));
      if (i == 12) continue;
      if (i < hour) element.appendChild(optionForm(i, "시", true));
      else element.appendChild(optionForm(i, "시", false));
    }
    
    element.addEventListener("focusout", (e) => {
      let minute = new Date().getMinutes();
      current = examineCurrentInterface(interfaces);
      let hourVal = element[element.options.selectedIndex].value;
      if (hourVal == "default") {
        return;
      }
      let minuteSelect = current.querySelector(".minute");
      minuteSelect.innerHTML = minuteDefaultOption;
      for (let i = 0; i < 60; i++) {
        if(i < 45 && i % 5 != 0 && hourVal != "08" && hourVal != "16") continue;
        if(hourVal == "11" && i > 50) continue;
        
        let flag = false;
        if (appointedTime[hourVal].includes(String(i).padStart(2, "0")) || (i < minute && Number(hourVal) == hour)){
          flag = true;
        }
        minuteSelect.appendChild(optionForm(i, "분", flag));
      }
    });
  });
};

const verifyBed = () => {
  bedNumImg.forEach((e) => {
    let inf = examineCurrentInterface(interfaces);
    if(inf.classList.value.includes('desktop')){
        e.src = `./image.resize/bedRemain0${bedNum}.reduct.png`;
    } else {
        e.src = `./image.resize/bedRemain0${bedNum}.reduct.png`;
    }
  });
};

const verifyDiagPos = () => {
  diagPosImg.forEach((e) => {
    let inf = examineCurrentInterface(interfaces);
    if(inf.classList.value.includes('desktop')){
        e.src = diagPos
          ? "./image.resize/diagPos.reduct.png"
          : "./image.resize/diagImpos.reduct.png";
    } else {
	e.src = diagPos
         ? "./image.resize/diagPos.reduct.png"
         : "./image.resize/diagImpos.reduct.png";
    }
  });
};

webIO.client.onopen = async () => {
  console.log("WebSocket Opened");
  await webIO.send({ enc: 0, type: 0, header: "s" });
};

webIO.client.onclose = () => {
  console.log("WebSocket Closed");
};

webIO.client.onmessage = async (data) => {
  let mes = JSON.parse(data.data);
  let message = JSON.parse(webIO.type_decrypt(mes));
  let stat = message["stat"];
  let head = message["content"]["header"];
  let returnType = message["content"]["body"]["return"];
  let innerData = message["content"]["body"]["body"];
  if (stat != 1) {
    errorHandling({ reload: true });
  } else {
    if (head == 6) {
      switch (returnType) {
        case 0:
          webIO.set_pubkey(innerData);
          let jsonContent = {
            "key": webIO.key,
            "iv": webIO.iv
          };
          await webIO.send({ enc: 1, type: 1, header: "s", body: jsonContent });
          break;
        case 1:
          data = copy(innerData);
          appointedTime = data["times"];
          diagPos = data["diagPos"];
          bedNum = data["bedNum"];
          verifyBed();
          verifyDiagPos();
          makeOptions();
          break;
        case 2:
          if (innerData == -1) {
            errorHandling({ message: "이미 신청된 시간입니다." });
          }
	  alert("신청되었습니다.");
          loading(true);
          break;
        default:
          errorHandling({ reload: true });
      }
    } else if (head == 2) {
      let t = innerData.split(":");
      appointedTime[t[0]].push(t[1]);
      makeOptions();
    } else if (head == 3 || head == 7) {
      innerData = innerData.split(":");
      appointedTime[innerData[0]] = appointedTime[innerData[0]].filter((e) => {
        return e != innerData[1];
      });
    } else if (head == 4) {
      bedNum = innerData;
      verifyBed();
    } else if (head == 5) {
      diagPos = innerData;
      verifyDiagPos();
    } else {
      errorHandling({ reload: true });
    }
  }
};

applyBtns.forEach((element) => {
  element.addEventListener("click", async (e) => {
    loading();
    current = examineCurrentInterface(interfaces);
    let applyForm = current.getElementsByClassName("apply")[0];

    let data = {
      number: applyForm.getElementsByClassName("number")[0],
      name: applyForm.getElementsByClassName("name")[0],
      sex: applyForm.getElementsByClassName("sex"),
      symptom: applyForm.getElementsByClassName("symptom")[0],
      otherSymptom: applyForm.getElementsByClassName("otherSymptom")[0],
      time: [
        applyForm.getElementsByClassName("hour")[0],
        applyForm.getElementsByClassName("minute")[0],
      ],
    };

    let verified;
    let err_flag = false;
    let message;
    try {
      verified = verify(data);
    } catch (err) {
      message = err.message;
      console.log(message);
      err_flag = true;
    }

    if (err_flag) {
      loading(true);
      errorHandling({
        message: `"${message}"를 입력하지 않았습니다. "${message}"를 입력해주세요.`,
        reload: false,
      });
      return false;
    }

    await webIO.send({ type: 2, header: "s", body: verified });
    return true;
  });
});

modal.querySelector("#symSubmit").addEventListener("click", (e) => {
  current = examineCurrentInterface(interfaces);
  const checkboxes = modal.getElementsByClassName("form-check-input");
  symptom = [];
  for (let box of checkboxes) {
    if (box.checked) {
      if (box.value == "그 외") {
        current.querySelector("#otherSymptomCover").removeAttribute("hidden");
        other = true;
      } else {
        symptom.push(box.value);
      }
    } else {
      if (box.value == "그 외") {
        current
          .querySelector("#otherSymptomCover")
          .setAttribute("hidden", true);
        other = false;
      }
    }
  }
  current.querySelector("#symptomInput").value = symptom.join(", ");
});

about.addEventListener("click", (e) => {
  location.replace(
    "https://docs.google.com/document/d/1degMd317t3KixcS9bujQ--YyTdfb7kVPpdHn9UZeeq8/edit?usp=sharing"
  );
});

names.forEach((name) => {
  document.getElementById(name).addEventListener("click", () => {
    location.href = `./html/${name}.html`;
  });
});

logo.addEventListener("click", () => {
  location.href = "./";
});

window.addEventListener('beforeunload', async (event) => {
  await webIO.close();
});
