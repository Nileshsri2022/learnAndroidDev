Here is a clear, structured breakdown and explanation of the tutorial on **setting up your first project in Android Studio**.

---

### **Overview**
This guide walks through creating a brand-new project in Android Studio from the initial welcome screen. It covers how to choose a project template, configure project settings, and understand important Android development concepts like **Package Names**, **SDKs**, and **API Levels**.

---

### **Step-by-Step: Creating Your First Project**

#### **1. The Welcome Screen & Customization**
Before creating a project, Android Studio offers several sidebar options:
* **Customize:** Allows you to change the color theme (e.g., Dark Theme/Darcula), font size (set to 13), and keyboard shortcuts (Keymap).
* **Plugins:** Marketplace for extensions and add-ons that add extra functionality to Android Studio.
* **Learn:** Links to official documentation, getting started guides, and Android Studio video tutorials.

---

#### **2. Selecting the Platform and Template**
When you click **"New Project"**:
1. **Target Platform:** You can build for *Phone & Tablet, Wear OS (watches), TV,* or *Automotive*. The tutorial selects **Phone and Tablet**.
2. **Templates:** Android Studio provides pre-written boilerplate code ("blueprints") for common app layouts.
   * **Selection:** Choose **Empty Activity** (the simplest and most common starting point for new apps).

---

#### **3. Configuring Project Details**
In the configuration screen, you define key properties for your app:

| Setting | Explanation | Example |
| :--- | :--- | :--- |
| **Name** | The visible name of your application. | `My First App` |
| **Package Name** | A unique identifier for your app on the Google Play Store. Written in **reverse domain name notation**. | `eu.tutorials.myfirstapp` or `com.example.myfirstapp` |
| **Save Location** | The folder on your computer where project files are stored. | `C:\Users\admin\AndroidStudioProjects\...` |
| **Minimum SDK** | The oldest version of Android that can run your app. | **API 24: Android 7.0 (Nougat)** |

---

### **Key Technical Concepts Explained**

#### **1. Package Name Structure**
* **Why it matters:** Every app published to the Google Play Store must have a globally unique package name.
* **Format:** `com.domain.appname` (Reverse URL).
  * Example: If your website is `tutorials.eu`, your package name becomes `eu.tutorials.myfirstapp`.

#### **2. SDK (Software Development Kit)**
* A collection of tools, code libraries, and documentation provided by Google that allows developers to build software for the Android platform.

#### **3. API Levels vs. Android Versions**
* **API Level:** Google’s internal integer numbering system for Android versions.
* Every major Android release increments the API level:
  * **API 21** = Android 5.0 (Lollipop)
  * **API 24** = Android 7.0 (Nougat) *(Chosen default)*
  * **API 34** = Android 14 (Upside Down Cake)

#### **4. Minimum SDK & Device Compatibility**
* Setting **API 24 (Android 7.0)** as the Minimum SDK ensures your app will run on approximately **95.4% of all active Android devices worldwide**.
* Choosing a **higher API** gives you access to newer Android features, but fewer older devices can install your app.
* Choosing a **lower API** supports more older devices, but restricts you from using modern Android features without backward-compatibility libraries.

---

#### **4. Building the Project (Gradle)**
* After clicking **Finish**, Android Studio downloads necessary dependencies and builds the project using **Gradle** (Android’s build automation system).
* Once the build finishes, the main workspace loads, ready for development.

---

### **Next Steps**
The next video/step will explore the **Android Studio User Interface (UI)**, including the project file tree, the code editor, and the layout designer.
