ECE Project Summary


Your project is a smart magnification system that dynamically adjusts on-screen content based on the user's viewing distance. The system combines hardware sensing with software-based display scaling to create an assistive tool for users who need variable screen magnification.

Hardware Component


Built using an Arduino Uno.

Uses an Ultrasonic Sensor (HC-SR04) to continuously measure the distance between the user and the laptop screen.

Sends real-time distance data to the software via serial communication.

Software Component


A custom-built desktop application that reads the Arduino’s distance data.

According to the distance and preset lens power, the app automatically magnifies or shrinks the screen content.

Magnification logic is calibrated so that the closer the user is, the lesser the magnification, and vice versa.

Objective


To provide a vision-assistive digital display tool that optimizes screen readability by dynamically adjusting magnification, ensuring comfortable viewing for users with different visual needs or lenses.

Outcome


The final system acts like a smart magnifier, bridging hardware sensing and software scaling to enhance accessibility and personalization of digital screens.
