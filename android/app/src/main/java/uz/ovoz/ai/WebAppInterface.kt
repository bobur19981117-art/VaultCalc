package uz.ovoz.ai

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.util.Base64
import android.webkit.JavascriptInterface
import android.widget.Toast
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStream

class WebAppInterface(private val context: Context) {

    private val mainHandler = Handler(Looper.getMainLooper())

    @JavascriptInterface
    fun showToast(message: String) {
        mainHandler.post {
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
        }
    }

    @JavascriptInterface
    fun saveMp3(base64Data: String, fileName: String) {
        try {
            val cleanBase64 = if (base64Data.contains(",")) {
                base64Data.substringAfter(",")
            } else {
                base64Data
            }

            val audioBytes = Base64.decode(cleanBase64, Base64.DEFAULT)
            val name = if (fileName.endsWith(".mp3", ignoreCase = true)) fileName else "$fileName.mp3"

            var savedSuccess = false

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val resolver = context.contentResolver
                val contentValues = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, name)
                    put(MediaStore.MediaColumns.MIME_TYPE, "audio/mpeg")
                    put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/OzbekOvozAI")
                }

                val uri: Uri? = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, contentValues)
                if (uri != null) {
                    resolver.openOutputStream(uri)?.use { outputStream: OutputStream ->
                        outputStream.write(audioBytes)
                        outputStream.flush()
                        savedSuccess = true
                    }
                }
            } else {
                val downloadsDir = File(
                    Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                    "OzbekOvozAI"
                )
                if (!downloadsDir.exists()) {
                    downloadsDir.mkdirs()
                }
                val destFile = File(downloadsDir, name)
                FileOutputStream(destFile).use { fos ->
                    fos.write(audioBytes)
                    fos.flush()
                    savedSuccess = true
                }
                MediaScannerConnection.scanFile(
                    context,
                    arrayOf(destFile.absolutePath),
                    arrayOf("audio/mpeg"),
                    null
                )
            }

            mainHandler.post {
                if (savedSuccess) {
                    Toast.makeText(
                        context,
                        "MP3 yuklab olindi: Download/OzbekOvozAI/$name",
                        Toast.LENGTH_LONG
                    ).show()
                } else {
                    Toast.makeText(context, "Faylni saqlashda xatolik yuz berdi", Toast.LENGTH_SHORT).show()
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            mainHandler.post {
                Toast.makeText(context, "Saqlash xatosi: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    @JavascriptInterface
    fun shareAudio(base64Data: String, fileName: String) {
        try {
            val cleanBase64 = if (base64Data.contains(",")) {
                base64Data.substringAfter(",")
            } else {
                base64Data
            }
            val audioBytes = Base64.decode(cleanBase64, Base64.DEFAULT)
            val name = if (fileName.endsWith(".mp3", ignoreCase = true)) fileName else "$fileName.mp3"

            val cacheFile = File(context.cacheDir, name)
            FileOutputStream(cacheFile).use { fos ->
                fos.write(audioBytes)
                fos.flush()
            }

            val uri: Uri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                cacheFile
            )

            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "audio/mpeg"
                putExtra(Intent.EXTRA_STREAM, uri)
                putExtra(Intent.EXTRA_SUBJECT, "O'zbek Ovoz AI Audio")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }

            val chooser = Intent.createChooser(shareIntent, "Audioni ulashish").apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(chooser)
        } catch (e: Exception) {
            e.printStackTrace()
            mainHandler.post {
                Toast.makeText(context, "Ulashishda xatolik: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }
}
