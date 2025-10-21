import React, { useState } from 'react';
import { Calendar, Clock, Users, BookOpen, Settings, Plus, Trash2 } from 'lucide-react';

export default function HomeschoolPlanner() {
  const [startTime, setStartTime] = useState('8:00');
  const [endTime, setEndTime] = useState('15:00');
  const [blockSize, setBlockSize] = useState(30);
  const [includeWeekend, setIncludeWeekend] = useState(false);
  const [backToBack, setBackToBack] = useState(false);
  
  const [kids, setKids] = useState(['']);
  const [subjects, setSubjects] = useState([
    { name: '', sessions: 3, duration: 60, kids: [] }
  ]);
  const [commitments, setCommitments] = useState([
    { day: 'Monday', time: '14:00', activity: '' }
  ]);
  
  const [schedule, setSchedule] = useState(null);

  const addKid = () => setKids([...kids, '']);
  const removeKid = (index) => setKids(kids.filter((_, i) => i !== index));
  const updateKid = (index, value) => {
    const newKids = [...kids];
    newKids[index] = value;
    setKids(newKids);
  };

  const addSubject = () => setSubjects([...subjects, { name: '', sessions: 3, duration: 60, kids: [] }]);
  const removeSubject = (index) => setSubjects(subjects.filter((_, i) => i !== index));
  const updateSubject = (index, field, value) => {
    const newSubjects = [...subjects];
    newSubjects[index][field] = value;
    setSubjects(newSubjects);
  };
  const toggleSubjectKid = (subjectIndex, kid) => {
    const newSubjects = [...subjects];
    const kidsList = newSubjects[subjectIndex].kids;
    if (kidsList.includes(kid)) {
      newSubjects[subjectIndex].kids = kidsList.filter(k => k !== kid);
    } else {
      newSubjects[subjectIndex].kids = [...kidsList, kid];
    }
    setSubjects(newSubjects);
  };

  const addCommitment = () => setCommitments([...commitments, { day: 'Monday', time: '14:00', activity: '' }]);
  const removeCommitment = (index) => setCommitments(commitments.filter((_, i) => i !== index));
  const updateCommitment = (index, field, value) => {
    const newCommitments = [...commitments];
    newCommitments[index][field] = value;
    setCommitments(newCommitments);
  };

  const generateSchedule = () => {
    const kidsList = kids.filter(k => k.trim());
    const validSubjects = subjects.filter(s => s.name.trim());
    const validCommitments = commitments.filter(c => c.activity.trim());
    
    if (kidsList.length === 0 || validSubjects.length === 0) {
      alert('Please add at least one child and one subject');
      return;
    }

    // Parse subjects with all kids if none selected
    const parsedSubjects = validSubjects.map(s => ({
      ...s,
      kids: s.kids.length > 0 ? s.kids : kidsList
    }));

    // Generate time slots
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    
    const timeSlots = [];
    for (let m = startMinutes; m < endMinutes; m += blockSize) {
      const h = Math.floor(m / 60);
      const min = m % 60;
      timeSlots.push(`${h.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`);
    }

    // Days of week
    const days = includeWeekend 
      ? ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
      : ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

    // Initialize schedule grid
    const grid = {};
    days.forEach(day => {
      grid[day] = {};
      kidsList.forEach(kid => {
        grid[day][kid] = {};
        timeSlots.forEach(time => {
          grid[day][kid][time] = null;
        });
      });
    });

    // Block out fixed commitments
    validCommitments.forEach(({ day, time, activity }) => {
      if (grid[day]) {
        kidsList.forEach(kid => {
          if (grid[day][kid][time] !== undefined) {
            grid[day][kid][time] = { subject: activity, fixed: true };
          }
        });
      }
    });

    // Schedule subjects with distribution across the week
    parsedSubjects.forEach(subject => {
      const blocksNeeded = Math.ceil(subject.duration / blockSize);
      const daysToUse = Math.min(subject.sessions, days.length);
      const dayInterval = Math.floor(days.length / daysToUse);
      
      let sessionsScheduled = 0;
      let dayIndex = 0;
      
      while (sessionsScheduled < subject.sessions && dayIndex < days.length) {
        const day = days[dayIndex];
        
        // Try to schedule one session on this day
        let scheduled = false;
        for (let i = 0; i <= timeSlots.length - blocksNeeded; i++) {
          // Check if all kids are available for all blocks
          let available = true;
          for (let kid of subject.kids) {
            if (!kidsList.includes(kid)) continue;
            for (let b = 0; b < blocksNeeded; b++) {
              const slot = timeSlots[i + b];
              if (!slot || grid[day][kid][slot] !== null) {
                available = false;
                break;
              }
            }
            if (!available) break;
          }

          if (available) {
            // Schedule this session
            subject.kids.forEach(kid => {
              if (kidsList.includes(kid)) {
                for (let b = 0; b < blocksNeeded; b++) {
                  const slot = timeSlots[i + b];
                  grid[day][kid][slot] = {
                    subject: subject.name,
                    shared: subject.kids.length > 1,
                    isStart: b === 0
                  };
                }
              }
            });
            sessionsScheduled++;
            scheduled = true;
            break;
          }
        }
        
        // Move to next day with distribution
        if (sessionsScheduled < subject.sessions) {
          if (scheduled && dayInterval > 0) {
            dayIndex += dayInterval;
          } else {
            dayIndex++;
          }
          
          // Wrap around if we've distributed across the week but need more sessions
          if (dayIndex >= days.length && sessionsScheduled < subject.sessions) {
            dayIndex = (dayIndex % days.length) + 1;
          }
        } else {
          break;
        }
      }
    });

    setSchedule({ grid, timeSlots, days, kids: kidsList });
  };

  const kidsList = kids.filter(k => k.trim());

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Calendar className="w-8 h-8 text-indigo-600" />
            <h1 className="text-3xl font-bold text-gray-800">Homeschool Planner</h1>
          </div>

          {/* Settings */}
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4" />
                Start Time
              </label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4" />
                End Time
              </label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Settings className="w-4 h-4" />
                Block Size (minutes)
              </label>
              <select
                value={blockSize}
                onChange={(e) => setBlockSize(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value={15}>15 min</option>
                <option value={30}>30 min</option>
                <option value={60}>60 min</option>
              </select>
            </div>
            <div className="flex items-center">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeWeekend}
                  onChange={(e) => setIncludeWeekend(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium text-gray-700">Include Weekends</span>
              </label>
            </div>
            <div className="flex items-center">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={backToBack}
                  onChange={(e) => setBackToBack(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium text-gray-700">Back-to-back Sessions</span>
              </label>
            </div>
          </div>

          {/* Children */}
          <div className="mb-6">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Users className="w-4 h-4" />
              Children
            </label>
            {kids.map((kid, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={kid}
                  onChange={(e) => updateKid(index, e.target.value)}
                  placeholder="Child's name"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                />
                {kids.length > 1 && (
                  <button
                    onClick={() => removeKid(index)}
                    className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={addKid}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-600 rounded-md hover:bg-indigo-200"
            >
              <Plus className="w-4 h-4" />
              Add Child
            </button>
          </div>

          {/* Subjects */}
          <div className="mb-6">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <BookOpen className="w-4 h-4" />
              Subjects
            </label>
            {subjects.map((subject, index) => (
              <div key={index} className="border border-gray-300 rounded-md p-4 mb-3">
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={subject.name}
                    onChange={(e) => updateSubject(index, 'name', e.target.value)}
                    placeholder="Subject name"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                  />
                  <button
                    onClick={() => removeSubject(index)}
                    className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">Sessions per week</label>
                    <input
                      type="number"
                      value={subject.sessions}
                      onChange={(e) => updateSubject(index, 'sessions', parseInt(e.target.value) || 0)}
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">Duration (minutes)</label>
                    <input
                      type="number"
                      value={subject.duration}
                      onChange={(e) => updateSubject(index, 'duration', parseInt(e.target.value) || 0)}
                      min="15"
                      step="15"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                {kidsList.length > 0 && (
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">Which children? (leave empty for all)</label>
                    <div className="flex flex-wrap gap-2">
                      {kidsList.map(kid => (
                        <label key={kid} className="flex items-center gap-1 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={subject.kids.includes(kid)}
                            onChange={() => toggleSubjectKid(index, kid)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm">{kid}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
            <button
              onClick={addSubject}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-600 rounded-md hover:bg-indigo-200"
            >
              <Plus className="w-4 h-4" />
              Add Subject
            </button>
          </div>

          {/* Fixed Commitments */}
          <div className="mb-6">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              Fixed Commitments
            </label>
            {commitments.map((commitment, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <select
                  value={commitment.day}
                  onChange={(e) => updateCommitment(index, 'day', e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="Monday">Monday</option>
                  <option value="Tuesday">Tuesday</option>
                  <option value="Wednesday">Wednesday</option>
                  <option value="Thursday">Thursday</option>
                  <option value="Friday">Friday</option>
                  <option value="Saturday">Saturday</option>
                  <option value="Sunday">Sunday</option>
                </select>
                <input
                  type="time"
                  value={commitment.time}
                  onChange={(e) => updateCommitment(index, 'time', e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md"
                />
                <input
                  type="text"
                  value={commitment.activity}
                  onChange={(e) => updateCommitment(index, 'activity', e.target.value)}
                  placeholder="Activity name"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                />
                <button
                  onClick={() => removeCommitment(index)}
                  className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            <button
              onClick={addCommitment}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-600 rounded-md hover:bg-indigo-200"
            >
              <Plus className="w-4 h-4" />
              Add Commitment
            </button>
          </div>

          <button
            onClick={generateSchedule}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-md transition-colors"
          >
            Generate Schedule
          </button>
        </div>

        {/* Schedule Display */}
        {schedule && (
          <div className="bg-white rounded-lg shadow-lg p-8 overflow-x-auto">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Weekly Schedule</h2>
            <div className="min-w-max">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border border-gray-300 bg-gray-100 p-2 text-left font-semibold sticky left-0 bg-gray-100">
                      Time
                    </th>
                    {schedule.days.map(day => (
                      <th key={day} colSpan={schedule.kids.length} className="border border-gray-300 bg-indigo-100 p-2 text-center font-semibold">
                        {day}
                      </th>
                    ))}
                  </tr>
                  <tr>
                    <th className="border border-gray-300 bg-gray-100 p-2 sticky left-0 bg-gray-100"></th>
                    {schedule.days.map(day => (
                      schedule.kids.map(kid => (
                        <th key={`${day}-${kid}`} className="border border-gray-300 bg-indigo-50 p-2 text-center text-sm">
                          {kid}
                        </th>
                      ))
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {schedule.timeSlots.map(time => (
                    <tr key={time}>
                      <td className="border border-gray-300 bg-gray-50 p-2 font-medium text-sm sticky left-0 bg-gray-50">
                        {time}
                      </td>
                      {schedule.days.map(day => (
                        schedule.kids.map(kid => {
                          const cell = schedule.grid[day][kid][time];
                          return (
                            <td
                              key={`${day}-${kid}-${time}`}
                              className={`border border-gray-300 p-2 text-center text-sm ${
                                cell?.fixed
                                  ? 'bg-red-100 font-semibold'
                                  : cell?.shared
                                  ? 'bg-green-100'
                                  : cell
                                  ? 'bg-blue-100'
                                  : ''
                              }`}
                            >
                              {cell?.isStart ? cell.subject : cell && !cell.fixed ? '↓' : cell?.subject || ''}
                            </td>
                          );
                        })
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-100 border border-gray-300"></div>
                <span>Individual Subject</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-100 border border-gray-300"></div>
                <span>Shared Subject</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-100 border border-gray-300"></div>
                <span>Fixed Commitment</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
