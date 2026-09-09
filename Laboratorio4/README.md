# Lab 4: RemoteSchooly

This laboratory specifies Balbuena EduKanvas from the RemoteSchooly case study using the
repository's Top-Down and R.E.D.A.L.E. structure.

## Structure

| Folder | Content |
| --- | --- |
| [`study-case/`](study-case/) | English translation of the assignment source and its pipeline image. |
| [`people/`](people/) | Government Teacher, Rural Teacher and Rural Student personas. |
| [`core/`](core/) | Product summary, problem, objective, scope, concepts, needs, decisions, experience, flows, phases and acceptance criteria. |
| [`requirements/`](requirements/) | Consolidated functional and non-functional backlogs. |
| [`agents/`](agents/) | Placeholder for the requirements evaluator. |
| [`reports/`](reports/) | Immutable future evaluation iterations. |

## Suggested reading order

1. Read the [case study](study-case/Lab%20%234-%20Arqui2026.2.md).
2. Review [`people/`](people/) and [`core/`](core/).
3. Review the final backlogs in [`requirements/`](requirements/).
4. Use [`agents/`](agents/) and [`reports/`](reports/) after the evaluator is defined.

## Architecture Diagram

```mermaid
graph TD
    %% Infraestructura
    subgraph Lima [National Cloud Server - Lima]
        Actor_Melchor([Melchor Profesor de Gobierno])
        L_Login[Login/Register Service]
        L_Chatbot[Chatbot Service]
        L_LLM[LLM API Service]
        L_Opt[Skills, System Prompt, Agents]
        L_Upload[Upload Bimestral Course Material Service]
        L_Observe[Observe Teacher Profile Service]
        L_BD[(BD)]
    end

    subgraph Sync [Sync & Retries]
        S_Chunk[Retry Chunk Service]
        S_Cron[Retry Cron Service]
        S_Manual[Retry Manual Service]
    end

    subgraph Interior [School Local Server - Interior]
        Actor_Gaspar([Gaspar Profesor rural])
        G_Login[Login/Register Service]
        G_Download[Download Bimestral Material Service]
        G_Classroom[Classroom Service]
        G_CreateTask[Create Task Service]
        G_Schedule[Schedule Service]
        G_Announcement[Announcement Service]
        G_Review[Task Submission Review Service]
        G_Comments[Task Comments Service]
        G_Grades[Grades Upload Service]
        G_BD[(BD)]

        Actor_Baltasar([Baltasar Estudiante])
        B_Login[Login/Register Service]
        B_Download[Download Student Courses Service]
        B_GetAssign[Get Student Assignments Service]
        B_GetScores[Get Student Scores Service]
        B_GetComments[Get Comments in Assignment Service]
        B_Notification[Notification Service]
        B_BD[(BD)]
    end

    %% Relaciones Usuarios
    Actor_Melchor --> L_Login
    Actor_Gaspar --> G_Login
    Actor_Baltasar --> B_Login

    %% Relaciones Melchor
    L_Login --> L_Chatbot
    L_Login --> L_BD
    L_Observe --> L_BD
    L_Opt --> L_LLM
    L_LLM --> L_Chatbot
    L_Chatbot --> L_Upload

    %% Relaciones Sync
    L_Upload -.-> S_Chunk
    S_Chunk <--> S_Cron
    S_Cron <--> S_Manual

    %% Relaciones Gaspar
    G_Login --> G_BD
    G_Login --> G_Download
    G_Login --> G_Grades
    S_Chunk -.-> G_Download
    G_Download --> G_Classroom
    G_Classroom --> G_CreateTask
    G_Classroom --> G_Schedule
    G_Classroom --> G_Announcement
    G_Schedule --> G_Review
    G_CreateTask --> G_Review
    G_Review --> G_Comments
    G_Grades -->|Se retorna a Lima las calificaciones| L_BD

    %% Relaciones Baltasar
    B_Login --> B_BD
    B_Login --> B_Download
    B_Download --> B_GetAssign
    B_GetAssign --> B_GetScores
    B_GetAssign --> B_GetComments
    
    %% Relaciones Notificaciones
    G_Announcement --> B_Notification
    G_CreateTask --> B_Notification
    G_Comments --> B_Notification
    B_GetScores --> B_Notification
    B_GetComments --> B_Notification

    %% Estilos de Nodos (Colores Excalidraw)
    classDef blueBlock fill:#a5d8ff,stroke:#1e1e1e,stroke-width:2px,color:#000000;
    classDef yellowDB fill:#ffec99,stroke:#1e1e1e,stroke-width:2px,color:#000000;

    class Actor_Melchor,L_Login,L_Chatbot,L_LLM,L_Opt,L_Upload,L_Observe blueBlock;
    class S_Chunk,S_Cron,S_Manual blueBlock;
    class Actor_Gaspar,G_Login,G_Download,G_Classroom,G_CreateTask,G_Schedule,G_Announcement,G_Review,G_Comments,G_Grades blueBlock;
    class Actor_Baltasar,B_Login,B_Download,B_GetAssign,B_GetScores,B_GetComments,B_Notification blueBlock;
    class L_BD,G_BD,B_BD yellowDB;
```
