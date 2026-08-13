function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Baocao_Tiendo");
  
  if (!sheet) {
    sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet("Baocao_Tiendo");
    sheet.appendRow([
      "Ngay", "Tram", "Doi_Tao", "Da keo cap", "so tu han noi", 
      "Ghi chú", "Ke hoach ngay", "Số đội", "Tên đội", "Trạm kéo", "Trạm hàn"
    ]);
  }
  
  var data = JSON.parse(e.postData.contents);
  
  sheet.appendRow([
    data.Ngay,
    data.Tram,
    data.Doi_Tao,
    data.Da_keo_cap,
    data.so_tu_han_noi,
    data.Ghi_chu,
    data.Ke_hoach_ngay,
    data.So_doi,
    data.Ten_doi,
    data.Tram_keo,
    data.Tram_han
  ]);
  
  return ContentService.createTextOutput(JSON.stringify({"status": "success"}))
                       .setMimeType(ContentService.MimeType.JSON);
}
