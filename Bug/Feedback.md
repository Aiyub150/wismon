### Hasil pengujian wismon

* 1. Menu Dashboard Tidak Sinkron
pada saat pengujian membandingkan bagian card CPU Usage dengan task manager hasilnya update data yang rentang waktunya sekitar 8 detik menggunakan stopwatch, seharusnya semua update data dilakukan setiap 1 detik dan agar ringan status CPU USAGE, MEMORY USAGE, STORAGE, NETWORK THROUGHPUTS bisa dilakukan dengan real-time tanpa perlu menyimpan beberapa status card tersebut ke databases. Hasilnya nanti akan mendapatkan update setiap 1 detik dari system windows. Namun, setelah di stop lalu menambahan .env semua status tersebut ter-update secara real time penyebab tersebut perlu dipastikan dan tidak mengganggu performa device (awalnya health score nya di 60, dan ketika dicoba ctrl + c dan menjalankan lagi naik menjadi 85 dan data update setiap 1 detik secara real-time)

* 2. Chart "CPU & Memory Real-Time Load (60s)" dan "Memory Allocation Trend"
- Chart dari kedua diagramnya over kebawah melebih cardnya
- card CPU & Memory Real-Time Load (60s) terlalu lebar sampai bisa geser ke kanan, sebaiknya card tersebut lebarnya dikurangi 10% 
- ketika pointer mengarahkan ke arah diagram, sebaiknya ditambahkan semacam hover yang menampilkan status lebih mendetail misalnya " 18% jam 14:40 " waktu nya diambil berdasarkan waktu sistem.

* 3. GPU Nvidia-entricc
Menu GPU harusnya menampilkan semua tipe GPU yang ada pada device, namun walaupun model nya terdeteksi masalahnya utillization, vram, dan temperature hanya dibuat untuk mendeteksi GPU Nvidia saja sehingga perlu dirubah agar mendeteksi semua GPU secara global (entah amd, intel, nvidia, atau entah integrated gpu atau discrete gpu, atau bahkan ada lebih dari 1 gpu harus dibuat dinamis dan global)

* 4. Storage Menu
- Menu pada sidebar ketika mengakses menu storage yang active storage analyzer dan storage, sebaiknya jadi satu menu saja jika memang di dalamnya isi contentnya sama.
- Live Disk Throughput Curve tidak muncul apapun, perlu dicek kembali source code nya apakah mendeteksi read atau write nya dengan benar atau tidak. atau justru hanya mendeteksi storage tipe tertentu maka harus dibuat global dan dinamis
- Storage Analyzer Insights (Safe Review Mode) sebaiknya ditambahkan tombol action "delete" untuk menghapus file yang memang tidak dibutuhkan, sehingga user tidak perlu mencarinya lagi cukup menekan delete dan file tersebut akan masuk ke recycle bin.

* 5. Network Menu
- Menu pada sidebar sebaiknya menampilkan satu menu saja yaitu Network dan ketika di klik akan masuk ke halaman network yang menampilkan semua card dan chart yang ada pada halaman network. bukan dibuat 3 menu yang berbeda misal network, connections, network analysis active semua ketika saya hanya menekan menu network. jika memang isi contentnya sama semua secara keseluruhan sebaiknya satu menu saja.
- Bandwidth Throughput (KB/s) chartnya tidak muncul apapun, sebaiknya perlu dipastikan kemana chart tersebut terhubung sampai tidak menampilkan apapun.

* 6. Proccess Menu
Ada satu process yang membuat kebingungan yaitu System Idle Proccess yang cpu nya sampai menampilkan mencapai 586% atau bisa ratusan persen. Perlu ada deskripsi yang menjelaskan pada setiap process yang ada.

* 7. Security
- jika dua menu pada bagian security isi contentnya sama semua cukup tampilkan satu menu saja yaitu Security Events. 
- Setiap user menekan resolve akan pindah ke log dengan status resolve, perlu dipastikan apakah hanya mengganti statusnya saja atau benar-benar bertindak memperbaiki dan menyesuaikan masalah yang tampil pada events

* 8. Analysis
- Performance aktif dan history aktif, sebaiknya cukup satu saja aktif yaitu performance aja sedangkan menu lainnya jika konten nya sama dihilangkan saja 
- Historical Telemetry Curve (SQLite DB) tidak tampila apapun, apakah harus menunggu lebih dari 1 jam baru muncul data ? atau ada yang salah dengan database nya?

* 9. Dahoo
- tombol maupun menu dahoo sebaiknya dihilangkan saja, cukup menggunakan chat ngambang yang ada di pojok kanan bawah
- Enable Cloud AI (Gemini) sebaiknya dihapus saja, karena tidak terlalu berguna (paling tidak setidaknya ketika cloud ai nya mati tidak menampilkan icon seperti ini) kalau memang tidak bisa terhubung atau tidak ada jaringan tinggal di alihkan ke response biasa dan jika sudah kembali terkoneksi maka alihkan ke mode Gemini. mungkin perlu ditambahkan sedikit optimasi atau pengecekan ulang apakah ketika menambahkan file .env sudah bisa terhubung dengan model? atau tidak perlu dihapus tombolnya tapi sebaiknya diperbaiki jika ditekan harusnya aktif, masalahnya user menekan tidak berubah apapun dan tidak ada notif apapun apakah beralih ke model gemini atau tidak.
- UI bagian chat sebaikny dibuat bubble seperti chat whatsapps, karena setiap user mengirimkan pesan tidak ada bubble chat begitupun respon ai tidak ada bubble chat sehingga tidak nyaman untuk dibaca dan dilihat.
- sebaiknya icon dahoo dibuatkan maskot serigala lucu dengan eksperesi sesuai dengan kondisi dan situasi device.

